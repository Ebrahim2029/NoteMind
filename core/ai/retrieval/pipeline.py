# core/ai/retrieval/pipeline.py
import logging
logger = logging.getLogger("my_app.core.ai.retrieval.pipeline")

from typing import Dict, List, Sequence, Optional
from core.ai.clients.base_embed_client import BaseEmbedClient
from core.ai.clients.chroma_client import ChromaClient
from core.ai.ranking.weighted_ranker import NoteCandidate, WeightedRanker
from app_config import app_settings
from core.ai.clients.openai_client import OpenAIClient

from typing import Sequence, Dict, Optional
from datetime import datetime, timezone

def assemble_prompt(
    question: str,
    notes: Sequence[Dict[str, object]],
    history: Optional[Sequence[Dict[str, str]]] = None,
    intents: Optional[Sequence[str]] = None,
    max_notes: int = 10,
    max_note_content: int = 800,
    quoted: bool = False,
) -> str:
    """
    Build the final prompt that blends:
      - user question
      - retrieved notes (title + snippet + metadata + timestamps in YYYY-MM-DD)
      - recent chat history (last up to 10 messages)
      - recent intents (last up to 3)
    """
    lines: list[str] = [f"User question: {question.strip()}"]

    # Session history
    if history:
        lines.append("Recent conversation (oldest → newest):")
        for m in history[-10:]:
            role = m.get("role", "user")
            content = (m.get("content") or "")[:400]
            lines.append(f"  [{role}] {content}")

    # Intents (hints)
    if intents:
        lines.append("Recent user intents (hints): " + ", ".join(intents[-3:]))

    # Helper: format timestamps
    def fmt_date(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        try:
            return str(value)[:10]  # fallback for string ISO
        except Exception:
            return None

    # Retrieved notes
    lines.append(f"Relevant notes (score ≥ threshold, max {max_notes}):")
    for n in notes[:max_notes]:
        title = n.get("title", "Untitled")
        content = (n.get("content") or "")[:max_note_content].strip()
        score = n.get("score")
        tags = n.get("tags")
        is_pinned = n.get("is_pinned")
        is_archived = n.get("is_archived")
        created_at = fmt_date(n.get("created_at"))
        updated_at = fmt_date(n.get("updated_at"))

        meta_parts = []
        if score is not None:
            meta_parts.append(f"score={score:.2f}")
        if tags:
            meta_parts.append(f"tags={tags}")
        if is_pinned:
            meta_parts.append("pinned")
        if is_archived:
            meta_parts.append("archived")
        if created_at:
            meta_parts.append(f"created={created_at}")
        if updated_at:
            meta_parts.append(f"updated={updated_at}")

        meta_str = f" ({', '.join(meta_parts)})" if meta_parts else ""
        lines.append(f"- {title}{meta_str}: {content}")

    lines.append("Answer concisely using only the provided notes and context.")
    return "\n".join(lines)

def _parse_ts(value):
    if not value:
        return None
    if isinstance(value, datetime):
        # If naive, set UTC
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        # If still naive, set UTC
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None
    
class RetrievalPipeline:
    """Embed → query Chroma → filter by threshold → rank → return top-ids."""

    def __init__(self, embed_client: BaseEmbedClient, chroma: ChromaClient):
        self.embed_client = embed_client
        self.chroma = chroma
        self.ranker = WeightedRanker()

    def retrieve_top(
        self,
        question: str,
        tenant_id: str,                  # 🔹 user_id as tenant
        notebook_name: Optional[str] = None,  # 🔹 optional collection scope
        top_k: int = 10,
        threshold: float = 0.70
    ) -> List[str]:
        
        
        try:
            embeds = self.embed_client.embed([question])
        except Exception as e:
            logger.debug(f"[RetrievalPipeline] Failed to generate embeddings: {e}")
            return []
        if not embeds or not embeds[0]:
            return []

        q_emb = embeds[0]
        collection_name = notebook_name 
        raw = self.chroma.query(
            tenant_id,
            app_settings.CHROMA_NAME_DATABASE,
            collection_name,
            q_emb,
            top_k,
        )
        if not raw:
            return []
        
        # Filter by similarity
        kept = [
            (nid, score, doc, meta)
            for nid, score, doc, meta in raw
            #if score >= threshold
        ]
        
        if not kept:
            return []

        # Build candidates for ranking
        candidates = [
            NoteCandidate(
                id=nid,
                created_at=_parse_ts(meta.get("created_at")),
                updated_at=_parse_ts(meta.get("updated_at")),
                last_accessed_at=_parse_ts(meta.get("last_accessed_at")),
                title=meta.get("title"),
                tags=meta.get("tags"),
                is_pinned=meta.get("is_pinned") == "True",
                is_archived=meta.get("is_archived") == "True",
                reminders=meta.get("reminders"),
                content=doc,
            )
            for nid, score, doc, meta in kept
        ]
        scores = [score for _, score, _, _ in kept]
        ranked = self.ranker.rank(candidates, scores)
        results = [
            {
                "id": c.id,
                "score": score,
                "title": c.title,
                "content": c.content,
                "tags": c.tags,
                "is_pinned": c.is_pinned,
                "is_archived": c.is_archived,
                "reminders": c.reminders,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "last_accessed_at": c.last_accessed_at,
            }
            for c, score in ranked
        ]
        return results
