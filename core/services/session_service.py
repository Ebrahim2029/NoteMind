import logging

from requests import session
logger = logging.getLogger("my_app.services.search_service")

from typing import Dict, List, Literal
from dataclasses import dataclass, asdict
from datetime import datetime, date, timezone
import json

from infrastructure.cache import redis_client
from utils.sanitizer import sanitize_text
from core.repositories.chat_repository import ChatRepository
from core.repositories.models.chat_models import ChatSession

SESSION_TTL_SECONDS = 15 * 60  # 15 minutes
MessageRole = Literal["user", "assistant", "system"]


@dataclass
class SessionMessage:
    role: MessageRole
    content: str
    ts: str  # ISO timestamp


# ---------- Redis Keys ----------
def _session_messages_key(session_id: str) -> str:
    return f"session:{session_id}:messages"


def _session_intents_key(session_id: str) -> str:
    return f"session:{session_id}:intents"


def _session_notes_key(session_id: str) -> str:
    return f"session:{session_id}:notes"


def _session_context_key(session_id: str) -> str:
    return f"session:{session_id}:context"


class SessionService:
    """
    Hybrid Session Service:
    - Redis: short-term memory (messages, intents, notes, context) with TTL.
    - Postgres: persistent logging of interactions for audit/analytics.
    """

    def __init__(self, redis=None):
        self.redis = redis or redis_client

    # ---------------- Messages ----------------
    def add_message(self, session_id: str, role: MessageRole, content: str) -> None:
        msg = SessionMessage(
            role=role,
            content=sanitize_text(content),
            ts=datetime.now(timezone.utc).isoformat(),
        )
        key = _session_messages_key(session_id)
        try:
            self.redis.lpush(key, self._encode(msg))
            self.redis.ltrim(key, 0, 9)
            self.redis.expire(key, SESSION_TTL_SECONDS)
        except Exception as e:
            logger.error(f"[SessionService] Failed to add message for session {session_id}: {e}", exc_info=True)
            return
    def _sanitize_notes(self, notes: List[Dict]) -> List[Dict]:
        """Ensure all values in notes are JSON serializable (convert datetimes)."""
        import datetime
        sanitized = []
        for note in notes:
            clean_note = {}
            for k, v in note.items():
                if isinstance(v, (datetime.datetime, datetime.date)):
                    clean_note[k] = v.isoformat()
                else:
                    clean_note[k] = v
            sanitized.append(clean_note)
        return sanitized
  
    @staticmethod
    def _safe_meta_value(v):
        """Ensure metadata values are JSON-safe (stringify datetimes, pass others unchanged)."""
        if isinstance(v, (datetime, date)):
            return v.isoformat()
        elif hasattr(v, "value"):  # Handle value objects like UserId, NoteId
            return str(v.value)
        elif isinstance(v, list):
            return [SessionService._safe_meta_value(item) for item in v]
        elif isinstance(v, dict):
            return {k: SessionService._safe_meta_value(val) for k, val in v.items()}
        return v

    def get_history(self, session_id: str) -> List[Dict]:
        key = _session_messages_key(session_id)
        try:
            items = self.redis.lrange(key, 0, 9) or []
            out: List[Dict] = []
            for b in items[::-1]:  # oldest → newest
                raw = self._decode(b)
                out.append(raw)
            if items:
                self.redis.expire(key, SESSION_TTL_SECONDS)
            logger.debug(f"[SessionService] Retrieved {len(out)} messages for session {session_id}")
            return out
        except Exception as e:
            logger.error(f"[SessionService] Failed to fetch history for session {session_id}: {e}", exc_info=True)
            return []

    # ---------------- Intents ----------------
    def add_intent(self, session_id: str, intent: str) -> None:
        intent = sanitize_text(intent).lower().strip()
        if not intent:
            return
        key = _session_intents_key(session_id)
        try:
            self.redis.lpush(key, intent)
            self.redis.ltrim(key, 0, 2)
            self.redis.expire(key, SESSION_TTL_SECONDS)
            logger.debug(f"[SessionService] Added intent for {session_id}: {intent}")

        except Exception as e:
            logger.error(f"[SessionService] Failed to add intent for session {session_id}: {e}", exc_info=True)

    def get_recent_intents(self, session_id: str) -> List[str]:
        key = _session_intents_key(session_id)
        try:
            items = self.redis.lrange(key, 0, 2) or []
            out = [self._to_str(x) for x in items]
            if items:
                self.redis.expire(key, SESSION_TTL_SECONDS)
            logger.debug(f"[SessionService] Retrieved {len(out)} intents for session {session_id}")
            return out[::-1]
        except Exception as e:
            logger.error(f"[SessionService] Failed to fetch intents for session {session_id}: {e}", exc_info=True)
 
            return []

    # ---------------- Notes ----------------
    def add_notes(self, session_id: str, notes: List[Dict]) -> None:
        key = _session_notes_key(session_id)
        try:
            self.redis.setex(
                key,
                SESSION_TTL_SECONDS,
                json.dumps(notes, default=self._safe_meta_value),
            )
            logger.debug(f"[SessionService] Added {len(notes)} notes for session {session_id}")

        except Exception as e:
            logger.error(f"[SessionService] Failed to add notes for session {session_id}: {e}", exc_info=True)


    def get_recent_notes(self, session_id: str) -> List[Dict]:
        key = _session_notes_key(session_id)
        try:
            raw = self.redis.get(key)
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.error(f"[SessionService] Failed to fetch notes for session {session_id}: {e}", exc_info=True)
        return []

    # ---------------- Context ----------------
    def add_context(self, session_id: str, ctx: Dict) -> None:
        key = _session_context_key(session_id)
        try:
            self.redis.setex(key, SESSION_TTL_SECONDS, json.dumps(ctx))
            logger.debug(f"[SessionService] Added context for session {session_id}: {ctx}")
        except Exception as e:
            logger.error(f"[SessionService] Failed to add context for session {session_id}: {e}", exc_info=True)

    def get_context(self, session_id: str) -> Dict:
        key = _session_context_key(session_id)
        try:
            raw = self.redis.get(key)
            if raw:
                ctx = json.loads(raw)
                logger.debug(f"[SessionService] Retrieved context for session {session_id}: {ctx}")
                return ctx
        except Exception as e:
            logger.error(f"[SessionService] Failed to fetch context for session {session_id}: {e}", exc_info=True)
        return {}

    # ---------------- Combined Helpers ----------------
    def add_interaction(self, session_id: str, question: str, answer: str) -> None:
        """Store both user + assistant messages in Redis"""
        self.add_message(session_id, "user", question)
        self.add_message(session_id, "assistant", answer)
        logger.debug(f"[SessionService] Added interaction for {session_id}: Q='{question[:50]}', A='{answer[:50]}'")


    def add_interaction_persistent(
        self,
        db,
        session_id: str,
        question: str,
        answer: str,
        notes: List[Dict],
        lang: str,
        quoted_note_id: str | None = None,
    ) -> None:
        
        """Also persist in Postgres for audit/analytics"""
        repo = ChatRepository(db)
        try:
            # Ensure chat session exists
            session = db.query(ChatSession).filter_by(id=session_id).first()
            if not session:
                # Here you must decide how to set user_id (claims.sub, etc.)
                # For now fallback to "system" if no user is available
                logger.info(f"[SessionService] Creating new ChatSession for {session_id}")
                session = repo.create_session(user_id="system")
                # Ensure the session_id matches
                session.id = session_id
                db.add(session)
                db.commit()

            repo.add_interaction(
                session_id,
                "user",
                question,
                extra_metadata={"language": lang},
                quoted_note_id=quoted_note_id,
            )
            repo.add_interaction(
                session_id,
                "assistant",
                answer,
                notes=[self._safe_meta_value(n) for n in notes],
                extra_metadata={"language": lang},
            )
            logger.info(f"[SessionService] Persisted interaction for {session_id} in Postgres")
        except Exception as e:
            logger.error(
                f"[SessionService] Failed to persist interaction for {session_id}: {e}",
                exc_info=True,
            )



    # ---------------- Helpers ----------------
    @staticmethod
    def _encode(msg: SessionMessage) -> str:
        return json.dumps(asdict(msg))

    @staticmethod
    def _decode(raw: bytes | str) -> Dict:
        s = raw.decode() if isinstance(raw, (bytes, bytearray)) else raw
        return json.loads(s)

    @staticmethod
    def _to_str(raw: bytes | str) -> str:
        return raw.decode() if isinstance(raw, (bytes, bytearray)) else str(raw)
