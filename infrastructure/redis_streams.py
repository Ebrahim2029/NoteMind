# infrastructure/redis_streams.py
import time
import redis
import os
from typing import Dict, Tuple, List

# Create dedicated Redis client for streams
streams_redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    #password=os.getenv('REDIS_PASSWORD') or None,
    decode_responses=False,  # ← Critical for streams
    socket_timeout=5,
    socket_connect_timeout=5
)

PROCESSED_KEY = "stream:processed"

def is_duplicate(xid: str, ttl: int = 3600) -> bool:
    """Check if xid already processed (idempotency)."""
    # Use the streams client for consistency
    ok = streams_redis_client.setnx(f"{PROCESSED_KEY}:{xid}", int(time.time()))
    if ok:
        streams_redis_client.expire(f"{PROCESSED_KEY}:{xid}", ttl)
        return False
    return True

def auto_claim(stream: str, group: str, consumer: str,
               min_idle_ms: int = 60000, count: int = 10):
    """Reclaim stale messages for this consumer."""
    try:
        msgs = streams_redis_client.xautoclaim(
            stream, group, consumer,
            min_idle_time=min_idle_ms,
            start_id="0", count=count
        )
        return msgs[1] if msgs else []
    except Exception:
        return []

def ack_safe(stream: str, group: str, xid: str):
    """Ack without throwing errors."""
    try:
        streams_redis_client.xack(stream, group, xid)
    except Exception:
        pass