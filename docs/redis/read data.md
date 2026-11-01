Got it 👍
You want to **read data from Redis normally**, and also **interact with Redis Streams** by creating a consumer group (`XGROUP CREATE`) and producing events (`XADD`). Then you want to be able to **read events** back.

Here’s a clean **Python example** using `redis-py` (`redis` package):

---

## 1️⃣ Setup Redis client

```python
import redis

# Connect to Redis (adjust host/port/db as needed)
r = redis.Redis(host="localhost", port=6379, decode_responses=True)
```

---

## 2️⃣ Add events to a Stream (`XADD`)

```python
# Stream name
stream_key = "notes:events"

# Add events to the stream
event_id1 = r.xadd(stream_key, {"action": "create", "note_id": "123", "content": "Hello world"})
event_id2 = r.xadd(stream_key, {"action": "update", "note_id": "123", "content": "Updated content"})

print("Added events:", event_id1, event_id2)
```

---

## 3️⃣ Create a Consumer Group (`XGROUP CREATE`)

```python
group_name = "sync-workers"

try:
    # Create consumer group starting from the beginning of the stream ($ for only new)
    r.xgroup_create(stream_key, group_name, id="0", mkstream=True)
    print(f"Group '{group_name}' created on stream '{stream_key}'")
except redis.exceptions.ResponseError as e:
    if "BUSYGROUP" in str(e):
        print(f"Group '{group_name}' already exists")
    else:
        raise
```

---

## 4️⃣ Read events

### Option A: Read without consumer group

```python
events = r.xread({stream_key: "0"})  # "0" means from the start
for stream, msgs in events:
    for msg_id, fields in msgs:
        print("Event:", msg_id, fields)
```

### Option B: Read with consumer group (`XREADGROUP`)

```python
consumer_name = "worker-1"

# Block until event comes (2000 ms = 2s)
events = r.xreadgroup(group_name, consumer_name, {stream_key: ">"}, count=10, block=2000)

for stream, msgs in events:
    for msg_id, fields in msgs:
        print(f"[{consumer_name}] Event:", msg_id, fields)
        # Acknowledge processing
        r.xack(stream_key, group_name, msg_id)
```

---

✅ With this flow:

1. `XADD` produces messages.
2. `XGROUP CREATE` initializes a group.
3. Consumers use `XREADGROUP` to process events.
4. You can still `xread` for raw inspection.

---

👉 Do you want me to also show you **how to list existing groups and consumers** (via `XINFO GROUPS` and `XINFO CONSUMERS`) so you can monitor them?
