"""
import logging
from fastapi import HTTPException
from app.constants.redis_errors import RedisErrors

logger = logging.getLogger("my_app.redis")

def emit_event(event: dict, stream: str = "notes:events"):
    try:
        # ... actual xadd call
        logger.info("Event emitted to stream")
    except Exception as e:
        logger.error(f"{RedisErrors.REDIS_STREAM_EMIT_FAILED}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "code": RedisErrors.REDIS_STREAM_EMIT_FAILED.name,
                "message": RedisErrors.REDIS_STREAM_EMIT_FAILED.value,
            }
        )
"""


from enum import Enum
from messages import Status


from enum import Enum
from .messages import Status

class RedisInfo(str, Enum):
    # ---------------- Status ----------------
    REDIS_STATUS_SUCCESS = Status.SUCCESS

    # ---------------- Connection ----------------
    REDIS_CONNECTION_ESTABLISHED = "Redis connection established"
    REDIS_CONNECTION_CLOSED = "Redis connection closed"
    REDIS_PING_SUCCESS = "Redis ping successful"
    REDIS_HEALTHY_STATUS = "Redis healthy status"

    # ---------------- Cache ----------------
    REDIS_CACHE_SET_SUCCESS = "Cache value set successfully"
    REDIS_CACHE_GET_SUCCESS = "Cache value retrieved successfully"
    REDIS_CACHE_DELETE_SUCCESS = "Cache key deleted successfully"
    REDIS_CACHE_REFRESH_TTL_SUCCESS = "Cache TTL refreshed successfully"
    REDIS_CACHE_HIT = "Cache hit"
    REDIS_CACHE_MISS = "Cache miss"

    # ---------------- Streams ----------------
    REDIS_STREAM_EMIT_SUCCESS = "Event emitted to Redis Stream successfully"
    REDIS_STREAM_READ_SUCCESS = "Redis Stream read successfully"
    REDIS_STREAM_ACK_SUCCESS = "Stream message acknowledged successfully"
    REDIS_STREAM_AUTOCLAIM_SUCCESS = "Stream message auto-claimed successfully"
    REDIS_STREAM_GROUP_CREATED = "Consumer group created successfully"
    REDIS_STREAM_PROCESSING_SUCCESS = "Stream message processed successfully"
    REDIS_STREAM_DLQ_WRITE_SUCCESS = "Message written to DLQ successfully"

    # ---------------- Outbox ----------------
    REDIS_OUTBOX_EMIT_SUCCESS = "Outbox event emitted successfully"
    REDIS_OUTBOX_PAYLOAD_ACCEPTED = "Outbox payload accepted successfully"

    # ---------------- Worker ----------------
    REDIS_WORKER_STARTED = "Redis worker started successfully"
    REDIS_WORKER_CLEANUP_SUCCESS = "Worker cleanup completed successfully"
    REDIS_WORKER_METRICS_FLUSHED = "Worker metrics flushed successfully"
    REDIS_WORKER_SHUTDOWN_CLEAN = "Worker shutdown cleanly"

    # ---------------- General ----------------
    REDIS_OPERATION_COMPLETED = "Redis operation completed successfully"

class RedisErrors(str, Enum):
    # ---------------- Status ----------------
    REDIS_STATUS_FAILED = Status.FAILED

    # ---------------- Connection ----------------
    REDIS_CONNECTION_FAILED = "Redis connection failed"
    REDIS_SERVICE_UNAVAILABLE = "Redis service unavailable"
    REDIS_REQUEST_TIMED_OUT = "Redis request timed out"
    REDIS_UNHEALTHY_STATUS = "Redis unhealthy status"

    # ---------------- Cache ----------------
    REDIS_CACHE_SET_FAILED = "Failed to set cache value"
    REDIS_CACHE_GET_FAILED = "Failed to get cache value"
    REDIS_CACHE_DELETE_FAILED = "Failed to delete cache key"
    REDIS_CACHE_REFRESH_TTL_FAILED = "Failed to refresh TTL for cache key"
    REDIS_CACHE_SERIALIZATION_ERROR = "Cache serialization error"
    REDIS_CACHE_DESERIALIZATION_ERROR = "Cache deserialization error"
    REDIS_CACHE_CORRUPTED_PAYLOAD = "Cache payload corrupted"
    REDIS_CACHE_KEY_TOO_LARGE = "Cache key size too large"

    # ---------------- Streams ----------------
    REDIS_STREAM_EMIT_FAILED = "Failed to emit event to Redis Stream"
    REDIS_STREAM_READ_FAILED = "Failed to read from Redis Stream"
    REDIS_STREAM_ACK_FAILED = "Failed to acknowledge stream message"
    REDIS_STREAM_AUTOCLAIM_FAILED = "Failed to auto-claim stream messages"
    REDIS_STREAM_DUPLICATE_CHECK_FAILED = "Failed to check duplicate stream ID"
    REDIS_STREAM_DLQ_WRITE_FAILED = "Failed to write message to DLQ"
    REDIS_STREAM_GROUP_CREATION_FAILED = "Failed to create consumer group"
    REDIS_STREAM_PROCESSING_ERROR = "Error processing Redis Stream message"
    REDIS_STREAM_RETRY_LIMIT_EXCEEDED = "Retry limit exceeded for Redis Stream message"

    # ---------------- Outbox ----------------
    REDIS_OUTBOX_EMIT_FAILED = "Failed to emit outbox event"
    REDIS_OUTBOX_PAYLOAD_INVALID = "Invalid outbox payload"

    # ---------------- Worker ----------------
    REDIS_WORKER_CLEANUP_FAILED = "Worker cleanup failed"
    REDIS_WORKER_METRICS_FLUSH_FAILED = "Worker metrics flush failed"
    REDIS_WORKER_SHUTDOWN_ERROR = "Worker shutdown error"

    # ---------------- General / Limits ----------------
    REDIS_MEMORY_LIMIT_EXCEEDED = "Redis memory limit exceeded"
    REDIS_DISK_LIMIT_EXCEEDED = "Redis disk limit exceeded"
    REDIS_REQUEST_RATE_LIMIT_EXCEEDED = "Redis request rate limit exceeded"
    REDIS_TOO_MANY_CONNECTIONS = "Too many concurrent Redis connections"
    REDIS_OPERATION_TOO_SLOW = "Redis operation too slow"
    REDIS_BATCH_REQUEST_TOO_LARGE = "Redis batch request too large"
    REDIS_UNKNOWN_INTERNAL_ERROR = "Unknown internal Redis error"
