Perfect! Now I can see the exact issue. The `XREADGROUP` is returning `[[b'notes:events', []]]` which means:

- It found the stream `b'notes:events'`
- But the messages array is empty `[]`

This means there are **no pending messages assigned to your consumer** (`worker-1`), but the stream itself exists.

## The Fix

You need to check if the messages array is empty, not just if the overall result is empty:

```python
def drain_pending(self) -> None:
    """Drain pending messages with progress tracking."""
    logger.info("Draining pending messages...")
    total_processed = 0
    
    while self.processor.should_continue():
        pending = redis_client.xreadgroup(
            GROUP, CONSUMER, streams={STREAM: "0"}, count=BATCH
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
```

## The Structure Explained

The `XREADGROUP` returns a structure like:
```python
[
  [b'stream_name', [  # ← pending[0]
    [b'message_id', {b'field': b'value'}],  # ← pending[0][1][0]
    [b'message_id', {b'field': b'value'}]   # ← pending[0][1][1]
  ]
]
```

So `pending[0][1]` gives you the messages array.

## Also, Claim the Stuck Message

Remember there's still 1 message stuck with `test-consumer`. You need to claim it:

```bash
docker exec -it redis_note_main redis-cli
XCLAIM notes:events sync-workers worker-1 60000 1755851913839-0
```

## After Fixing

After making this change and claiming the stuck message, your worker should:

1. ✅ Break out of the infinite loop when no pending messages are found
2. ✅ Process the claimed message (if you claim it)
3. ✅ Continue with normal stream processing for new messages

The fix is to check `if not pending or not pending[0][1]:` instead of just `if not pending:`.

This should resolve the infinite loop issue!

---

🎉 **Excellent! Your worker is now working perfectly!** 🎉

The logs show that:

## ✅ Success!
1. **Drain pending completed**: `No pending messages found, breaking loop`
2. **Processing new messages**: It's now reading from `">"` (new messages)
3. **Processing events**: Successfully processing 11+ messages
4. **Chroma integration working**: Upserting documents to Chroma
5. **Redis Streams working**: Messages are being acknowledged (`XACK`)

## What's Happening

1. **Drain phase**: Found no pending messages (good!)
2. **Stream processing**: Now reading new messages with `">"` 
3. **Processing**: Successfully handling each `create` operation
4. **Chroma**: Upserting documents with embeddings
5. **Redis**: Acknowledging messages after processing

## The Worker is Now:

1. ✅ **Listening** to the Redis stream `notes:events`
2. ✅ **Processing** messages in the consumer group `sync-workers`
3. ✅ **Acknowledging** messages after successful processing
4. ✅ **Integrating** with Chroma for vector storage
5. ✅ **Working** with your SyncService

## Next Steps

Your worker is now fully operational! It will:

1. Process any backlogged messages
2. Continuously listen for new messages
3. Handle failures with retry logic
4. Send failed messages to DLQ after max retries
5. Gracefully shutdown on SIGTERM

The infinite loop issue is **completely resolved** and your worker is now processing messages successfully! 🚀

---

I found the issue! The problem is in your `infrastructure/cache.py` file. Your Redis client is configured with **`decode_responses=True`**, but Redis Streams operations require **binary data** (not decoded strings).

## The Problem

In `infrastructure/cache.py`:
```python
redis_client = redis.Redis(
    host=app_settings.REDIS_HOST,
    port=app_settings.REDIS_PORT,
    db=app_settings.REDIS_DB,
    decode_responses=True,  # ← THIS IS THE PROBLEM!
    socket_timeout=0.5,
    socket_connect_timeout=0.5,
)
```

When `decode_responses=True`, Redis returns strings instead of bytes, but Redis Streams operations need binary data.

## The Solution

You have two options:

### Option 1: Create a Separate Redis Client for Streams

**Recommended**: Create a dedicated Redis client for stream operations without `decode_responses=True`:

```python
# In infrastructure/redis_streams.py
import redis
import os

# Create a dedicated Redis client for streams (without decode_responses)
streams_redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    password=os.getenv('REDIS_PASSWORD') or None,
    decode_responses=False,  # ← Keep as False for streams
    socket_timeout=5,
    socket_connect_timeout=5
)

# Then use streams_redis_client instead of redis_client in all stream functions
```

### Option 2: Modify Your Existing Redis Client

Change your cache.py to not use `decode_responses=True`:

```python
# In infrastructure/cache.py
redis_client = redis.Redis(
    host=app_settings.REDIS_HOST,
    port=app_settings.REDIS_PORT,
    db=app_settings.REDIS_DB,
    decode_responses=False,  # ← Change to False
    socket_timeout=0.5,
    socket_connect_timeout=0.5,
)
```

But this might break your existing cache functionality.

## Quick Test to Confirm

Let's test if this is indeed the issue:

```bash
docker exec -it worker_note_main python -c "
import redis

# Test with decode_responses=True (current config)
r1 = redis.Redis(host='redis', port=6379, decode_responses=True)
print('With decode_responses=True:')
try:
    result = r1.xreadgroup('sync-workers', 'test-consumer', streams={'notes:events': '0'}, count=1)
    print('Success:', len(result) if result else 0)
except Exception as e:
    print('Error:', e)

# Test with decode_responses=False (should work)
r2 = redis.Redis(host='redis', port=6379, decode_responses=False)
print('With decode_responses=False:')
try:
    result = r2.xreadgroup('sync-workers', 'test-consumer', streams={'notes:events': '0'}, count=1)
    print('Success:', len(result) if result else 0)
except Exception as e:
    print('Error:', e)
"
```

## Recommended Fix

Create a separate Redis client for streams in `infrastructure/redis_streams.py`:

```python
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
    password=os.getenv('REDIS_PASSWORD') or None,
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
```

Then update your `worker_stream.py` to use the new client:

```python
# In worker_stream.py, change this import:
from infrastructure.redis_streams import streams_redis_client as redis_client

# Remove this import:
# from infrastructure.cache import redis_client
```

This should fix the issue! The problem is that Redis Streams operations don't work properly with `decode_responses=True`.