# core/services/sync_service.py

import logging
logger = logging.getLogger("my_app.services.sync_service")

import datetime
import ast
from typing import Dict, Iterable
from datetime import datetime
from core.ai.clients.base_embed_client import BaseEmbedClient
from core.ai.clients.chroma_client import ChromaClient
from utils.chunker.chunk_sentence import chunk_text
from infrastructure.cache import redis_client
from utils.cache_keys import (
    invalidation_for_create_note, invalidation_for_update_note, invalidation_for_delete_note
)
from app_config import app_settings


def _safe_meta_value(v):
    """Ensure metadata values are JSON-safe (stringify datetimes, pass others unchanged)."""
    if isinstance(v, datetime):
        return v.isoformat()
    elif hasattr(v, 'value'):  # Handle value objects like UserId, NoteId
        return str(v.value)
    elif isinstance(v, (list, dict)):
        # Ensure nested structures are also serializable
        if isinstance(v, list):
            return [_safe_meta_value(item) for item in v]
        elif isinstance(v, dict):
            return {key: _safe_meta_value(value) for key, value in v.items()}
    return v


class SyncService:
    def __init__(self, embed_client: BaseEmbedClient, chroma: ChromaClient, redis=None):
        self.embed_client = embed_client
        self.chroma = chroma
        self.redis = redis or redis_client

    # ---------------- Main Dispatcher ----------------
    def handle(self, event: Dict) -> None:
       
        logger.info(f"[SyncService] Handling event: {event.get('op')} | payload={event}")
        op = event.get("op")
        logger.info(f"[SyncService] Handling event: {op} | payload={event}")

        try:
            if op.startswith("user_"):
                logger.info(f"[SyncService] Handling user event: {op}")
                self._handle_user_event(event)

            elif op.startswith("notebook_"):
                logger.info(f"[SyncService] Handling notebook event: {op}")
                self._handle_notebook_event(event)

            elif op in {"create", "update", "upsert", "delete"}:
                logger.info(f"[SyncService] Handling note event: {op}")
                self._handle_note_event(event)
            else:
                logger.warning(f"[SyncService] Unknown event op={op}")
        except Exception as e:
            logger.error(f"[SyncService] Failed to handle event op={op}, err={e}", exc_info=True)

    # ---------------- User Events ----------------
    # emit_event({"op": "user_update", "user_id": str(uid), "username": updated.username})
    def _handle_user_event(self, e: Dict) -> None:
        user_id = str(e.get("user_id"))
        op = e["op"]
        user_name = e.get("username")
        if op == "user_create":
            logger.info(f"[SyncService] Ensuring tenant for user={user_id}")
            self.chroma.tenants.create(user_id)
            self.chroma.databases.create(user_id, app_settings.CHROMA_NAME_DATABASE)
        elif op == "user_delete":
            logger.info(f"[SyncService] User delete → no direct Chroma delete (tenants kept for now)")
            self.chroma.tenants.delete(user_id)
        elif op == "user_update":
            logger.info(f"[SyncService] User update → no Chroma action needed")
            self.chroma.tenants.update(user_id, user_name)
        self._purge_patterns([f"user:{user_id}*"])

    # ---------------- Notebook Events ----------------
    def _handle_notebook_event(self, e: Dict) -> None:
        # emit_event({"op": "notebook_create", "notebook_id": str(nid)})
        # emit_event({"op": "notebook_update", "notebook_id": str(nid)})
        # emit_event({"op": "notebook_delete", "notebook_id": str(notebook_id)})
        """
        [SyncService] Handling event: notebook_create | 
        payload={
            'op': 'notebook_create', 
            'user_id': 'de8f2693-9e88-4fb4-a945-8bfbe96eddbe', 
            'notebook_id': 'c7334d7a-29ec-48cd-b569-30463aa6df57', 
            'name': 'Scincesame schema Notebook', 
            'created_at': '2025-08-28T22:05:16.912000'}
        """
        nid = str(e.get("notebook_id"))
        tenant_id = str(e.get("user_id"))
        name_notebook = e.get("name")
        created_at = e.get("created_at")
        meta = {"title": name_notebook, "created_at": created_at}
        op = e["op"]
        if op == "notebook_create":
            self.chroma.collections.create(tenant_id, app_settings.CHROMA_NAME_DATABASE, nid, meta)
        elif op == "notebook_delete":
            logger.info(f"[SyncService] Notebook delete id={nid} → TODO: optionally drop collection")
            self.chroma.collections.delete(nid)
        elif op == "notebook_update":
            logger.info(f"[SyncService] Notebook update id={nid} (metadata only)")
            self.chroma.collections.update(nid, metadata=e.get("metadata"))
        self._purge_patterns([f"notebook:{nid}*"])

    # ---------------- Note Events ----------------
    def _handle_note_event(self, e: Dict) -> None:
        op = e.get("op")
        if op == "delete":
            self._handle_delete(e)
        elif op == "create":
            self._handle_upsert(e)
        elif op == "update":
            self._handle_upsert(e)

    
    def _handle_upsert(self, e: Dict) -> None:
        note_id = str(e["note_id"])
        user_id = str(e["user_id"])
        notebook_id = str(e.get("notebook_id"))
        content = e.get("content", "")
        title = e.get("title", "")
        created_at = e.get("created_at", "")
        updated_at = e.get("updated_at", "")
        is_archived = e.get("is_archived", False)
        is_pinned = e.get("is_pinned", False)
        reminders = e.get("reminders", None)
        tags = e.get("tags", [])
        version = e.get("version", 1)

        # 1. Split content into semantic chunks
        chunks = chunk_text(content, chunk_size=800, overlap=10)
        
        # 2. Build inputs (text for embedding)
        inputs = [
            f"Title: {title} {c}"
            for c in chunks
        ]

 
        # 3. Build metadata for each chunk
        metadatas = [
            {
                "note_id": note_id,
                "chunk_index": i,
                "notebook_id": notebook_id,
                "user_id": user_id,
                "title": title,
                "tags": tags,
                "is_archived": is_archived,
                "is_pinned": is_pinned,
                "reminders": reminders,
                "created_at": created_at,   #"created_at": _safe_meta_value(e.get("created_at")),
                "updated_at": updated_at,   #"updated_at": _safe_meta_value(e.get("updated_at")),
                "version": version,
            }
            for i in range(len(chunks))
        ]
        
        # 4. Build ids for Chroma
        ids = [f"{note_id}_{i}" for i in range(len(chunks))]

        # Debug: print chunk info
        for i, c in enumerate(chunks):
            logger.debug(f"[SyncService] Chunk {i}: {c[:80]}...")


        # 5. Embed the inputs
        try:
            embeddings = self.embed_client.embed(inputs)
        except Exception as embed_error:
            logger.error(f"[SyncService] Embedding failed: {embed_error}")
            return


        #  Ensure we have valid embeddings
        if not embeddings or not all(isinstance(emb, list) and len(emb) > 0 for emb in embeddings):
            logger.error(f"[SyncService] Invalid embeddings received: {len(embeddings)}")
            return

        #  Ensure length consistency - move this check AFTER embeddings are validated
        if len(chunks) != len(embeddings):
            logger.error(f"[SyncService] Embedding/chunk length mismatch: chunks={len(chunks)}, embeddings={len(embeddings)}")
            return
        
        #  Final length check (all should be equal now)
        if len(ids) != len(embeddings) or len(ids) != len(metadatas):
            logger.error(f"[SyncService] Final length mismatch: ids={len(ids)}, emb={len(embeddings)}, meta={len(metadatas)}")
            return
            
        logger.info(
            f"[SyncService] Prepared upsert: ids={len(ids)}, emb={len(embeddings)}, meta={len(metadatas)} "
            f"| first_id={ids[0] if ids else None}, first_meta={metadatas[0] if metadatas else None}"
        )

        # Debug logging
        logger.info(f"[SyncService] Upserting note={note_id} user={user_id} "
                    f"chunks={len(chunks)} sample_meta={metadatas[0]}")

        # Send to Chroma
        self.chroma.upsert(
            tenant_id=user_id, 
            collection_name=notebook_id,
            db_name=app_settings.CHROMA_NAME_DATABASE,
            documents=inputs,
            note_ids=ids,
            embeddings=embeddings,
            metadatas=metadatas
        )

        patterns = (
            invalidation_for_create_note(user_id)
            if e["op"] == "create"
            else invalidation_for_update_note(note_id, user_id)
        )
        self._purge_patterns(patterns)

    def _handle_delete(self, e: Dict) -> None:
        note_id = str(e["note_id"])
        user_id = str(e["user_id"])
        notebook_id = str(e.get("notebook_id", "default"))
        logger.info(f"[SyncService] Deleting note={note_id} user={user_id}")
        self.chroma.delete(user_id, "smart_notes", notebook_id, [note_id])
        self._purge_patterns(invalidation_for_delete_note(note_id, user_id))

    # ---------------- Cache helpers ----------------
    def _purge_patterns(self, patterns: Iterable[str]) -> None:
        if not self.redis:
            return
        try:
            for pat in patterns:
                cursor = 0
                while True:
                    cursor, keys = self.redis.scan(cursor=cursor, match=pat, count=100)
                    if keys:
                        self.redis.delete(*keys)
                    if cursor == 0:
                        break
        except Exception as e:
            logger.error(f"[SyncService] Cache purge failed: {e}", exc_info=True)
