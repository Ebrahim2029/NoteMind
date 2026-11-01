"""
NoteRepository with cache-first get_by_id and outbox-friendly writes.
"""
import logging
logger = logging.getLogger("my_app.repositories.note_repository")

from typing import Dict, Iterable, Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from core.repositories.base_repository import BaseRepository
from core.repositories.mixins.cache_mixin import CacheMixin
from infrastructure.cache import CacheKeys
from utils.outbox import emit_event

from core.repositories.models.note_models import NoteModel  # SQLAlchemy ORM
from core.repositories.models.notebook_models import NotebookModel
from core.entities.note import Note, NoteId, Timestamp
from datetime import datetime, timezone 


class NoteRepository(BaseRepository, CacheMixin):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    # --------- Public API ---------
    def get_by_id(self, note_id: UUID) -> Optional[Note]:
        key = CacheKeys.NOTE_BY_ID.format(note_id=note_id)
        return self.get_cached(key, lambda: self._load_note_by_id(note_id))

    def create(self, entity: Note) -> Note:
        with self._transaction():
            db_obj = self._to_db_model(entity)
            self.db.add(db_obj)
            self.db.flush()
            created = self._to_entity(db_obj)

             # Resolve user_id via notebook
            user_id = None
            if created.notebook_id:
                user_id = self.db.query(NotebookModel.user_id).filter(
                    NotebookModel.id == created.notebook_id
                ).scalar()


            # Invalidate cache & emit event for sync worker
            self.invalidate_keys(CacheKeys.NOTE_BY_ID.format(note_id=created.id.value))

            emit_event({
                "op": "create",
                "note_id": str(created.id.value),
                "notebook_id": str(created.notebook_id),
                "user_id":str(user_id),
                "title": created.title,
                "content": created.content,
                "created_at": created.created_date,
                "updated_at": created.modified_date,
                "is_archived": created.is_archived,
                "is_pinned": created.is_pinned,
                "reminders": created.reminder,
                "tags": created.tags,
                "version": getattr(db_obj, "version", 1),
            })
      
            return created

    def update(self, entity: Note) -> Note:
        with self._transaction():
            db_obj: NoteModel = self.db.query(NoteModel).filter(NoteModel.id == entity.id.value).first()
            if not db_obj:
                raise ValueError("Note not found")
            db_obj.title = entity.title
            db_obj.content = entity.content
            db_obj.tags = entity.tags
            db_obj.color = entity.color
            db_obj.is_pinned = entity.is_pinned
            db_obj.is_archived = entity.is_archived
            db_obj.is_deleted = entity.is_deleted
            db_obj.attachments = entity.attachments

            # # optionally bump version if you keep an int version field
            # if hasattr(db_obj, "version") and isinstance(db_obj.version, int):
            #     db_obj.version += 1
            self.db.flush()
            updated = self._to_entity(db_obj)
            
            # Resolve user_id via notebook
            user_id = None
            if updated.notebook_id:
                user_id = self.db.query(NotebookModel.user_id).filter(
                    NotebookModel.id == updated.notebook_id
                ).scalar()
            
            self.invalidate_keys(CacheKeys.NOTE_BY_ID.format(note_id=updated.id.value))

            # keep in cache + cache event
            emit_event({
                "op": "update",
                "note_id": str(updated.id.value),
                "user_id": str(getattr(db_obj, "user_id", "") or ""),
                "title": updated.title,
                "content": updated.content,
                "version": getattr(db_obj, "version", 1),
            })
            return updated

    def delete(self, note_id: UUID) -> None:
        with self._transaction():
            obj: NoteModel = self.db.query(NoteModel).filter(NoteModel.id == note_id).first()
            if not obj:
                return


                # Resolve user_id via notebook
            user_id = None
            if obj.notebook_id:
                user_id = self.db.query(NotebookModel.user_id).filter(
                    NotebookModel.id == obj.notebook_id
                ).scalar()
                
            self.db.delete(obj)
            self.db.flush()
            self.invalidate_keys(CacheKeys.NOTE_BY_ID.format(note_id=note_id))
            emit_event({"op": "delete", "note_id": str(note_id), "user_id": str(user_id or "")})

    # --------- Internal helpers ---------
    def _load_note_by_id(self, note_id: UUID) -> Optional[Note]:
        obj: Optional[NoteModel] = self.db.query(NoteModel).filter(NoteModel.id == note_id).first()
        return self._to_entity(obj) if obj else None

    @staticmethod
    def _to_entity(obj: Optional[NoteModel]) -> Optional[Note]:
        if not obj:
            return None
        # Map ORM → domain
        # Domain Note expects value objects for id/timestamps; pass through and rely on constructors.
        return Note(
            id=NoteId(value=str(obj.id)),
            notebook_id=obj.notebook_id,
            title=obj.title,
            content=obj.content,
            tags=obj.tags or [],
            color=obj.color,
            is_pinned=obj.is_pinned,
            is_archived=obj.is_archived,
            is_deleted=obj.is_deleted,
            reminder=obj.reminder,
            attachments=obj.attachments or [],
            created_date=obj.created_at,
            modified_date=obj.updated_at,
        )

    @staticmethod
    def _to_db_model(entity: Note) -> NoteModel:
        return NoteModel(
            id=entity.id.value if hasattr(entity.id, "value") else entity.id,
            notebook_id=entity.notebook_id,
            title=entity.title,
            content=entity.content,
            tags=entity.tags or [],
            color=entity.color,
            is_pinned=entity.is_pinned,
            is_archived=entity.is_archived,
            is_deleted=entity.is_deleted,
            reminder=entity.reminder,
            attachments=entity.attachments or [],
        )
    
        # ---- Cache overrides ----
    def _serialize(self, obj: Note) -> str:  # type: ignore[override]
        data = {
            "id": obj.id.value if hasattr(obj.id, "value") else str(obj.id),
            "notebook_id": getattr(obj, "notebook_id", None),
            "title": obj.title,
            "content": obj.content,
            "tags": obj.tags or [],
            "color": obj.color,
            "is_pinned": obj.is_pinned,
            "is_archived": obj.is_archived,
            "is_deleted": obj.is_deleted,
            "reminder": getattr(obj, "reminder", None),
            "attachments": obj.attachments or [],
            "created_at": getattr(getattr(obj, "created_date", None), "value", None),
            "updated_at": getattr(getattr(obj, "modified_date", None), "value", None),
        }
        return super()._serialize(data)

    def _deserialize(self, data: str) -> Note:  # type: ignore[override]
        raw = super()._deserialize(data)
        return Note(
            id=NoteId(value=str(raw["id"])),
            notebook_id=raw.get("notebook_id"),
            title=raw["title"],
            content=raw["content"],
            tags=raw.get("tags", []) or [],
            color=raw["color"],
            is_pinned=raw["is_pinned"],
            is_archived=raw["is_archived"],
            is_deleted=raw["is_deleted"],
            reminder=raw.get("reminder"),
            attachments=raw.get("attachments", []) or [],
            created_date=Timestamp(value=raw.get("created_at")),
            modified_date=Timestamp(value=raw.get("updated_at")),
        )

        # --------- Bulk/meta helpers for search hydration ---------
    def get_by_ids(self, ids: Iterable[UUID]) -> List[Note]:
        """Load multiple notes; cache still applies per note via get_by_id()."""
        out: List[Note] = []
        for nid in ids:
            n = self.get_by_id(nid)
            if n:
                out.append(n)
        return out

    def get_meta_lookup(self, ids: Iterable[UUID]) -> Dict[str, dict]:
        """
        Return metadata needed by the ranker:
          { "<id>": {"created_at": dt|None, "updated_at": dt|None, "last_accessed_at": dt|None,
                     "title": str, "content": str } }
        """
        meta: Dict[str, dict] = {}
        for n in self.get_by_ids(ids):
            meta[str(n.id.value)] = {
                "created_at": getattr(getattr(n, "created_date", None), "value", None),
                "updated_at": getattr(getattr(n, "modified_date", None), "value", None),
                # May be None if not tracked in DB yet
                "last_accessed_at": getattr(getattr(n, "last_accessed", None), "value", None)
                if hasattr(n, "last_accessed") else None,
                "title": n.title,
                "content": n.content,
            }
        return meta

    def touch_accessed(self, note_id: UUID) -> None:
        """
        Update last_accessed_at in DB if the column exists; otherwise no-op.
        Safe in tests and in prod even if the schema hasn’t added the column yet.
        """
        with self._transaction():
            obj: NoteModel | None = self.db.query(NoteModel).filter(NoteModel.id == note_id).first()
            if not obj:
                return
            try:
                # Optional column — update only if present on the ORM
                if hasattr(obj, "last_accessed_at"):
                    obj.last_accessed_at = datetime.now(timezone.utc)
                # Flush but don’t emit outbox (access doesn’t change embeddings)
                self.db.flush()
            except Exception:
                # Silently ignore if schema doesn’t support this yet
                pass