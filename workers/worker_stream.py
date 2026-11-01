"""
Redis Streams consumer for note sync with production-grade XACK pattern.

- Reads events from stream `notes:events`
- Applies them via SyncService (Chroma upsert/delete + cache invalidation)
- At-least-once delivery with XREADGROUP + XACK
- Failed events go to DLQ (notes:events:dlq)
- Comprehensive retry logic with exponential backoff
"""

import logging

logger = logging.getLogger("my_app.sync_worker")


import os
import signal
import time
from typing import Any, Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass

from infrastructure.redis_streams import streams_redis_client as redis_client
from core.services.sync_service import SyncService
from core.ai.clients.openai_embed_client import OpenAIEmbedClient
from core.ai.clients.chroma_client import ChromaClient
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


# -------------------------------------
# Stub embedder (replace in production)
# -------------------------------------
# class _StubEmbed(BaseEmbedClient):
#     def _do_embed(self, texts: List[str]):
#         return [[(len(t) % 10) / 10.0] * 16 for t in texts]

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
        # Add connection closing, file cleanup, etc.
    
    def _flush_metrics(self) -> None:
        """Flush any pending metrics before shutdown."""
        logger.info("Flushing metrics...")
        # Add metrics reporting logic
    
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
        """Get current retry count for a message."""
        retry_key = f"retry:{STREAM}:{message_id}"
        retries = redis_client.get(retry_key)
        return int(retries) if retries else 0
    
    def _increment_retry_count(self, message_id: str) -> int:
        """Increment and get retry count for a message."""
        retry_key = f"retry:{STREAM}:{message_id}"
        retries = redis_client.incr(retry_key)
        redis_client.expire(retry_key, 3600)  # 1 hour TTL
        return retries
    
    def _reset_retry_count(self, message_id: str) -> None:
        """Reset retry count for a message."""
        retry_key = f"retry:{STREAM}:{message_id}"
        redis_client.delete(retry_key)
    
    def _process_message(self, fields: Dict[str, Any]) -> ProcessingResult:
        """Process a single message with proper error handling."""
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
            
            # Determine if this is a retryable error
            should_retry = not isinstance(e, (KeyboardInterrupt, SystemExit))
            dlq_reason = "max_retries_exceeded" if not should_retry else None
            
            return ProcessingResult(
                success=False,
                should_retry=should_retry,
                error_message=error_msg,
                dlq_reason=dlq_reason
            )
    
    def _handle_dlq(self, message_id: str, fields: Dict[str, Any], reason: str) -> None:
        """Send message to Dead Letter Queue."""
        try:
            # Add metadata about the failure
            dlq_fields = fields.copy()
            dlq_fields["dlq_reason"] = reason
            dlq_fields["failed_at"] = int(time.time())
            dlq_fields["original_message_id"] = message_id
            
            redis_client.xadd(DLQ_STREAM, dlq_fields, maxlen=10000, approximate=True)
            logger.warning(f"Sent message {message_id} to DLQ: {reason}")
            
        except Exception as e:
            logger.error(f"Failed to send message {message_id} to DLQ: {e}")
    
    def _process_with_retry(self, stream: str, message_id: str, fields: Dict[str, Any]) -> bool:
        """Process message with retry logic and proper XACK handling."""
        # Skip duplicates
        if is_duplicate(message_id):
            logger.info(f"Skipping duplicate message {message_id}")
            ack_safe(stream, GROUP, message_id)
            return True
        
        retry_count = self._get_retry_count(message_id)
        
        # Check if max retries exceeded
        if retry_count >= self.retry_config.max_retries:
            logger.error(f"Max retries exceeded for message {message_id}")
            self._handle_dlq(message_id, fields, "max_retries_exceeded")
            ack_safe(stream, GROUP, message_id)
            self._reset_retry_count(message_id)
            return False
        
        # Process the message
        result = self._process_message(fields)
        
        if result.success:
            # Success - acknowledge and cleanup
            ack_safe(stream, GROUP, message_id)
            self._reset_retry_count(message_id)
            logger.info(f"Successfully processed message {message_id}")
            return True
        else:
            # Failure - handle retry or DLQ
            if result.should_retry:
                new_retry_count = self._increment_retry_count(message_id)
                delay = self.processor.calculate_retry_delay(new_retry_count)
                
                logger.warning(
                    f"Processing failed for message {message_id}, "
                    f"retry {new_retry_count}/{self.retry_config.max_retries}, "
                    f"next retry in {delay}ms"
                )
                
                # Leave unacked for automatic retry
                return False
            else:
                # Non-retryable error - send to DLQ
                self._handle_dlq(message_id, fields, result.dlq_reason or "non_retryable_error")
                ack_safe(stream, GROUP, message_id)
                self._reset_retry_count(message_id)
                return False
    
    def _process_batch(self, entries: List) -> Tuple[int, int]:
        """Process a batch of messages and return success/failure counts."""
        success_count = 0
        failure_count = 0
        
        for stream, items in entries:
            for message_id, fields in items:
                if not self.processor.should_continue():
                    break
                
                try:
                    success = self._process_with_retry(stream, message_id, fields)
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                        
                except Exception as e:
                    logger.error(f"Unexpected error processing message {message_id}: {e}")
                    failure_count += 1
                    # Leave message unacked for retry
        
        return success_count, failure_count
    
    def drain_pending(self) -> None:
        """Drain pending messages with progress tracking."""
        logger.info("Draining pending messages...")
        total_processed = 0
        
        while self.processor.should_continue():
            # CHANGE THIS LINE: Use "0" instead of "0"
            pending = redis_client.xreadgroup(
                GROUP, CONSUMER, streams={STREAM: "0"}, count=BATCH  # ← Fixed
            )

            # Check if we got an empty messages array
            if not pending or not pending[0][1]:  # Check if messages array is empty
                logger.info("No pending messages found, breaking loop")
                break
            success_count, failure_count = self._process_batch(pending)
            total_processed += success_count + failure_count
            
            logger.info(
                f"Drained {total_processed} messages "
                f"(success: {success_count}, failed: {failure_count})"
            )
    
    def process_stream(self) -> None:
        """Main stream processing loop with comprehensive monitoring."""
        logger.info(f"Worker {CONSUMER} listening on {STREAM} in group {GROUP}")
        
        self.ensure_group()
        self.drain_pending()

        total_processed = 0
        batch_count = 0
        
        try:
            while self.processor.should_continue():
                batch_count += 1
                
                # Reclaim idle pending messages (this already works well)
                reclaimed = auto_claim(STREAM, GROUP, CONSUMER, min_idle_ms=60000, count=BATCH)
                if reclaimed:
                    logger.info(f"Auto-claim reclaimed {len(reclaimed)} stuck messages")
                    success_count, failure_count = self._process_batch([(STREAM, reclaimed)])
                    total_processed += success_count + failure_count
                
                # Normal consumption of new messages
                entries = redis_client.xreadgroup(
                    GROUP, CONSUMER, streams={STREAM: ">"}, count=BATCH, block=BLOCK_MS
                )
                
                if not entries:
                    continue
                
                success_count, failure_count = self._process_batch(entries)
                total_processed += success_count + failure_count
                
                # Log progress periodically
                if batch_count % 10 == 0:
                    logger.info(
                        f"Processed {total_processed} total messages "
                        f"(last batch: success={success_count}, failed={failure_count})"
                    )

        except Exception as e:
            logger.error(f"Stream processing error: {e}", exc_info=True)
        finally:
            self.processor.execute_cleanup()
            logger.info(f"Sync worker stopped gracefully. Total processed: {total_processed}")