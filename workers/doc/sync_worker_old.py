"""
Redis Streams consumer for note sync.

- Reads events from stream `notes:events`
- Applies them via SyncService (Chroma upsert/delete + cache invalidation)
- At-least-once delivery with XREADGROUP + XACK
- Failed events go to DLQ (notes:events:dlq)
"""



import os
import signal
import logging
from typing import Any, Dict, List

from infrastructure.cache import redis_client
from core.services.sync_service import SyncService
from core.ai.clients.base_embed_client import BaseEmbedClient
from core.ai.clients.chroma_client import ChromaClient
from infrastructure.redis_streams import is_duplicate, ack_safe, auto_claim
# -------------------------------------
# Redis Stream config
# -------------------------------------
STREAM = os.getenv("NOTES_STREAM", "notes:events")
DLQ_STREAM = f"{STREAM}:dlq"  # dead-letter stream for failed events
BLOCK_MS = int(os.getenv("STREAM_BLOCK_MS", "2000"))
BATCH = int(os.getenv("STREAM_BATCH", "100"))
GROUP = os.getenv("STREAM_GROUP", "sync-workers")
CONSUMER = os.getenv("STREAM_CONSUMER", f"worker-{os.getpid()}")

# Logging
logger = logging.getLogger("sync_worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# -------------------------------------
# Stub embedder (replace in production)
# -------------------------------------
class _StubEmbed(BaseEmbedClient):
    def _do_embed(self, texts: List[str]):
        return [[(len(t) % 10) / 10.0] * 16 for t in texts]

# -------------------------------------
# Consumer group setup
# -------------------------------------
def ensure_group() -> None:
    try:
        redis_client.xgroup_create(STREAM, GROUP, id="$", mkstream=True)
        logger.info(f"Created consumer group {GROUP} on {STREAM}")
    except Exception:
        # If group already exists, ignore
        pass

running = True

def _handle_sigterm(signum, frame):
    """Graceful shutdown handler."""
    global running
    running = False

# -------------------------------------
# Main loop
# -------------------------------------
def main():
    logger.info(f"Worker {CONSUMER} listening on {STREAM} in group {GROUP}")
    signal.signal(signal.SIGINT, _handle_sigterm)
    signal.signal(signal.SIGTERM, _handle_sigterm)

    ensure_group()
    svc = SyncService(embed_client=_StubEmbed(), chroma=ChromaClient(), redis=redis_client)

    # Drain pending (recover unacked)
    while running:
        pending = redis_client.xreadgroup(
            GROUP, CONSUMER, streams={STREAM: "0"}, count=BATCH
        )
        if not pending:
            break
        _process_and_ack(svc, pending)

    # Normal consumption
    while running:

        # Reclaim idle pending
        reclaimed = auto_claim(STREAM, GROUP, CONSUMER, min_idle_ms=60000, count=BATCH)
        if reclaimed:
            _process_and_ack(svc, [(STREAM, reclaimed)])
        
        # Normal consumption
        entries = redis_client.xreadgroup(
            GROUP, CONSUMER, streams={STREAM: ">"}, count=BATCH, block=BLOCK_MS
        )
        if not entries:
            continue
        _process_and_ack(svc, entries)

    logger.info("Sync worker stopped gracefully.")

# -------------------------------------
# Processing
# -------------------------------------
MAX_RETRIES = 3  # after this, send to DLQ

def _process_and_ack(svc: SyncService, entries: List):
    """
    Process events from Redis stream and ack if successful.
    On repeated failure, push event to DLQ.
    """
    #logger.info(f"[Worker] Processing {len(entries)} entries")
    for stream, items in entries:
        for xid, fields in items:

             #  Skip duplicates
            if is_duplicate(xid):
                logger.info(f"[Worker] Skipping duplicate {xid}")
                ack_safe(STREAM, GROUP, xid)
                continue
            try:
                event = {k.decode() if isinstance(k, bytes) else k:
                        _parse_val(v.decode() if isinstance(v, bytes) else v)
                        for k, v in fields.items()}
                logger.info(f"[Worker] Processing event: {event}")
                svc.handle(event)  # may raise
                ack_safe(STREAM, GROUP, xid)
            except Exception as e:
                logger.error(f"[Worker] Error processing event {fields} (xid={xid}): {e}", exc_info=True)

                # Track retry count using Redis hash
                retry_key = f"retry:{STREAM}:{xid}"
                retries = redis_client.incr(retry_key)
                redis_client.expire(retry_key, 3600)  # keep retry state for 1h

                if retries > MAX_RETRIES:
                    # Push to DLQ and ack original
                    logger.error(f"[Worker] Sending event to DLQ after {retries} retries: {fields}")
                    redis_client.xadd(DLQ_STREAM, fields, maxlen=10000, approximate=True)
                    redis_client.xack(STREAM, GROUP, xid)
                    redis_client.delete(retry_key)  # cleanup retry counter
                # else: leave unacked → will retry later

# -------------------------------------
# Helpers
# -------------------------------------
def _parse_val(v: Any) -> Any:
    """
    Convert Redis string values into Python types (basic).
    - "true"/"false" → bool
    - everything else stays string
    """
    s = v if isinstance(v, str) else str(v)
    if s in ("true", "false"):
        return s == "true"
    return s

if __name__ == "__main__":
    main()
