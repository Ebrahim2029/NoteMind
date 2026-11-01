"""
Redis Streams consumer for note sync with production-grade XACK pattern.

- Reads events from stream `notes:events`
- Applies them via SyncService (Chroma upsert/delete + cache invalidation)
- At-least-once delivery with XREADGROUP + XACK
- Failed events go to DLQ (notes:events:dlq)
- Comprehensive retry logic with exponential backoff
"""



import os
import logging
import time
from typing import Any, Dict, List, Tuple, Optional
from dataclasses import dataclass

from infrastructure.redis_streams import streams_redis_client as redis_client
from core.services.sync_service import SyncService
from core.ai.clients.chroma_client import ChromaClient
from core.ai.clients.openai_embed_client import OpenAIEmbedClient
from infrastructure.redis_streams import is_duplicate, ack_safe, auto_claim
from .stream_processor import StreamProcessor, RetryConfig

# -------------------------------------
# Redis Stream config
# -------------------------------------
STREAM = os.getenv("NOTES_STREAM", "notes:events")
DLQ_STREAM = f"{STREAM}:dlq"  # dead-letter stream for failed events
BLOCK_MS = int(os.getenv("STREAM_BLOCK_MS", "2000"))
BATCH = int(os.getenv("STREAM_BATCH", "100"))
GROUP = os.getenv("STREAM_GROUP", "sync-workers")
CONSUMER = os.getenv("STREAM_CONSUMER", f"worker-{os.getpid()}")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY_MS = int(os.getenv("RETRY_DELAY_MS", "1000"))

# Logging
logger = logging.getLogger("sync_worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# -------------------------------------
# Data classes for message tracking
# -------------------------------------
@dataclass
class ProcessingResult:
    success: bool
    should_retry: bool = True
    error_message: Optional[str] = None
    dlq_reason: Optional[str] = None


# -------------------------------------
# Sync Worker Class with Production XACK Pattern
# -------------------------------------
class SyncWorker:
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_config = retry_config or RetryConfig(
            max_retries=MAX_RETRIES,
            retry_delay_ms=RETRY_DELAY_MS,
            exponential_backoff=True
        )

        self.processor = StreamProcessor(self.retry_config)
        # 🔹 Always use OpenAI embeddings
        self.svc = SyncService(
            embed_client=OpenAIEmbedClient(),
            chroma=ChromaClient(),
            redis=redis_client
        )

        # Add cleanup handlers
        self.processor.add_cleanup_handler(self._cleanup)
        self.processor.add_cleanup_handler(self._flush_metrics)

    def _cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Performing worker cleanup...")

    def _flush_metrics(self) -> None:
        """Flush any pending metrics before shutdown."""
        logger.info("Flushing metrics...")

    def ensure_group(self) -> None:
        """Ensure consumer group exists."""
        try:
            redis_client.xgroup_create(STREAM, GROUP, id="$", mkstream=True)
            logger.info(f"Created consumer group {GROUP} on {STREAM}")
        except Exception as e:
            logger.info(f"Consumer group {GROUP} already exists on {STREAM}: {e}")

    def _parse_val(self, v: Any) -> Any:
        """Convert Redis string values into Python types."""
        s = v if isinstance(v, str) else str(v)
        if s in ("true", "false"):
            return s == "true"
        return s

    def _get_retry_count(self, message_id: str) -> int:
        retry_key = f"retry:{STREAM}:{message_id}"
        retries = redis_client.get(retry_key)
        return int(retries) if retries else 0

    def _increment_retry_count(self, message_id: str) -> int:
        retry_key = f"retry:{STREAM}:{message_id}"
        retries = redis_client.incr(retry_key)
        redis_client.expire(retry_key, 3600)  # 1 hour TTL
        return retries

    def _reset_retry_count(self, message_id: str) -> None:
        retry_key = f"retry:{STREAM}:{message_id}"
        redis_client.delete(retry_key)

    def _process_message(self, fields: Dict[str, Any]) -> ProcessingResult:
        try:
            event = {
                k.decode() if isinstance(k, bytes) else k:
                self._parse_val(v.decode() if isinstance(v, bytes) else v)
                for k, v in fields.items()
            }

            logger.info(f"Processing event: {event}")
            self.svc.handle(event)

            return ProcessingResult(success=True, should_retry=False)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing event: {error_msg}", exc_info=True)
            should_retry = not isinstance(e, (KeyboardInterrupt, SystemExit))
            dlq_reason = "max_retries_exceeded" if not should_retry else None
            return ProcessingResult(False, should_retry, error_msg, dlq_reason)

    def _handle_dlq(self, message_id: str, fields: Dict[str, Any], reason: str) -> None:
        try:
            dlq_fields = fields.copy()
            dlq_fields["dlq_reason"] = reason
            dlq_fields["failed_at"] = int(time.time())
            dlq_fields["original_message_id"] = message_id
            redis_client.xadd(DLQ_STREAM, dlq_fields, maxlen=10000, approximate=True)
            logger.warning(f"Sent message {message_id} to DLQ: {reason}")
        except Exception as e:
            logger.error(f"Failed to send message {message_id} to DLQ: {e}")

    # ... rest of class unchanged ...
