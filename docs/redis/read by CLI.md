Perfect 👍 you want the same thing (**produce + create group + read events**) but **directly in `redis-cli`** instead of Python.
Here’s how you can do it step by step:

---

## 1️⃣ Add events to a Stream (`XADD`)

```bash
# Add first event
XADD notes:events * action create note_id 123 content "Hello world"

# Add another event
XADD notes:events * action update note_id 123 content "Updated content"
```

👉 `*` lets Redis assign an auto-generated ID.

---

## 2️⃣ Create a Consumer Group (`XGROUP CREATE`)

```bash
# Create consumer group 'sync-workers' starting from the beginning
XGROUP CREATE notes:events sync-workers 0 MKSTREAM
```

* `notes:events` → stream name
* `sync-workers` → group name
* `0` → read from beginning (`$` would mean only new messages)
* `MKSTREAM` → create the stream if it doesn’t exist

If you run it again and the group exists, Redis will return an error.

---

## 3️⃣ Read events (without group)

```bash
# Read all messages from start
XREAD COUNT 10 STREAMS notes:events 0
```

---

## 4️⃣ Read events (with group)

```bash
# Read using consumer group
XREADGROUP GROUP sync-workers worker-1 COUNT 10 STREAMS notes:events >

# After processing, ACK the message:
XACK notes:events sync-workers <message-id>
```

---

## 5️⃣ Inspect groups & consumers

```bash
# List groups on a stream
XINFO GROUPS notes:events

# List consumers in a group
XINFO CONSUMERS notes:events sync-workers

# See stream info
XINFO STREAM notes:events
```

---

✅ With these commands, you can **XADD → XGROUP CREATE → XREADGROUP → XACK** all from `redis-cli`.

Do you want me to also give you a **ready-made redis-cli script** (like a sequence of commands you can paste directly) to test the full flow end-to-end?

---

Nice 👌 you just checked your **consumer group state** with `XINFO`. Let’s break it down line by line.

---

## 🔎 `XINFO GROUPS notes:events`

```
1) "name"              → sync-workers   (the group name)
2) "consumers"         → 2              (two consumers joined this group)
3) "pending"           → 8              (8 messages delivered but NOT yet acknowledged with XACK)
4) "last-delivered-id" → 1755714781068-0 (the last event ID the group delivered)
5) "entries-read"      → 34             (total entries the group has read so far)
6) "lag"               → 0              (how many new entries are still waiting to be delivered to this group)
```

👉 So your **group** `sync-workers` has 2 consumers. They’ve been delivered 34 messages, 8 of which are still **pending** (unacknowledged).

---

## 🔎 `XINFO CONSUMERS notes:events sync-workers`

You see details **per consumer** inside the group:

### Consumer 1

```
"name"      → worker-1
"pending"   → 8          (this consumer has 8 unacknowledged messages)
"idle"      → 98423 ms   (~98 seconds since last command from this consumer)
"inactive"  → 115825 ms  (~115 seconds since consumer was last seen active)
```

➡️ `worker-1` got messages but hasn’t ACKed them yet. That’s why pending=8.
It’s been idle for \~98s.

---

### Consumer 2

```
"name"      → worker-993b9d70cf47
"pending"   → 0          (this consumer has no unacknowledged messages)
"idle"      → 187251484 ms (~52 hours since last activity)
"inactive"  → 187317385 ms (~52 hours since last active in group)
```

➡️ This one connected long ago, but basically isn’t processing anymore. It’s idle for 2+ days.

---

## ⚡ Summary

* **Group**: `sync-workers`

  * Has 2 consumers.
  * Total 8 messages are pending acknowledgment.
  * No lag (all messages have been delivered to consumers).

* **Consumer `worker-1`**

  * Currently responsible for 8 unacknowledged messages.
  * Idle \~98s.

* **Consumer `worker-993b9d70cf47`**

  * Stale/inactive.
  * No messages pending.

---

💡 If you don’t `XACK` messages, they stay in **Pending Entries List (PEL)**.
You can inspect them with:

```bash
XPENDING notes:events sync-workers
```

This will show **which messages are pending, who owns them, and for how long**.

---

Do you want me to also show you how to **reclaim those 8 pending messages** (so another consumer can process them) using `XCLAIM` / `XAUTOCLAIM`?

---

Perfect 👌 now you’re looking at the **Pending Entries List (PEL)** for your group `sync-workers`. Let’s decode what `XPENDING` showed:

---

## 🔎 Output of `XPENDING notes:events sync-workers`

```
1) (integer) 8             → total pending messages = 8
2) "1755588932331-0"       → the smallest (oldest) pending message ID
3) "1755714781068-0"       → the largest (newest) pending message ID
4) 1) 1) "worker-1"
      2) "8"
```

* **8** → total number of messages pending acknowledgement in this group.
* **1755588932331-0 → 1755714781068-0** → the range of pending message IDs.
* **worker-1 → 8** → all 8 pending messages belong to consumer `worker-1`.

---

## 🔎 What does “pending” mean?

* These 8 messages were **delivered** to `worker-1` using `XREADGROUP`.
* But they were **never acknowledged** with `XACK`.
* Redis thinks they are still “in-flight” and may need retry or reassignment.

---

## ⚡ Next steps

### 1️⃣ Inspect details of pending messages

```bash
XPENDING notes:events sync-workers - + 10
```

* `- +` → from oldest to newest
* `10` → max number of entries to return

This shows each message ID, which consumer has it, how long it’s pending (ms), and number of deliveries.

---

### 2️⃣ Re-assign (claim) stuck messages

If `worker-1` is dead or not processing anymore, you can reclaim them:

```bash
XCLAIM notes:events sync-workers new-worker 60000 <message-id>
```

* `60000` → messages idle for more than 60s
* `<message-id>` → one of the pending IDs (e.g., `1755588932331-0`)
* `new-worker` → the consumer who will take over

Or automatically claim a batch:

```bash
XAUTOCLAIM notes:events sync-workers new-worker 60000 -
```

This will move all messages pending >60s to `new-worker`.

---

### 3️⃣ Acknowledge when done

Once processed, mark them as done:

```bash
XACK notes:events sync-workers <message-id>
```

This removes them from the Pending Entries List.

---

✅ So in your case:

* You have **8 stuck messages** owned by `worker-1`.
* They’ll remain “pending” until `worker-1` (or another consumer via `XCLAIM/XAUTOCLAIM`) processes and `XACK`s them.

---

Do you want me to write you a **ready-to-use Redis CLI sequence** that will:

1. Show pending details,
2. Reassign them to a new consumer,
3. And acknowledge them after processing?
