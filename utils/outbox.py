"""
Simple Redis Streams outbox producer.

Stream name suggestions:
- "notes:events"
Event examples:
- {"op":"create","note_id":"...","user_id":"...","title":"..","version":1}
- {"op":"update","note_id":"...","user_id":"..."}
- {"op":"delete","note_id":"...","user_id":"..."}
"""



import logging

from typing import Dict
from infrastructure.cache import redis_client  # infrastructure/cache.py alias
logger = logging.getLogger(__name__)

DEFAULT_STREAM = "notes:events"


def emit_event(event: Dict, stream: str = DEFAULT_STREAM) -> None:
    """
    XADD to Redis stream. Swallows errors to avoid blocking writes.
    """
    logger.info(f"[Outbox] Emitting event to {stream}: {event}")
    try:
        # Redis Stream requires string fields; cast all values
        # MAXLEN keeps only the last N entries. Keeps roughly 10000 entries, dropping old ones.
        fields = {k: ("" if v is None else str(v)) for k, v in event.items()}
        redis_client.xadd(stream, fields, maxlen=10000, approximate=True)
        logger.info(f"[Outbox] Successfully emitted event to {stream}")
    except Exception as e:
        logger.warning(f"[Outbox] Failed to emit event to {stream}: {e}")
        logger.exception("[Outbox] Exception occurred")
