# README — 03. Redis & Caching Playbook

> Scope: Redis for dev/prod, service management, CLI usage, caching strategies for FastAPI/Postgres, persistence, monitoring, and troubleshooting.

---

## 1) Service Management (systemd-based hosts)

| Command                        | What it does         | Notes                                          |
| ------------------------------ | -------------------- | ---------------------------------------------- |
| `sudo systemctl status redis`  | Check service status |                                                |
| `sudo systemctl start redis`   | Start service        |                                                |
| `sudo systemctl stop redis`    | Stop service         |                                                |
| `sudo systemctl restart redis` | Restart              |                                                |
| `sudo systemctl enable redis`  | Auto-start on boot   |                                                |
| `sudo systemctl disable redis` | Disable on boot      |                                                |
| `sudo journalctl -u redis -f`  | Tail logs            | Add `--since=1h` / `--until=…` for time window |

---

## 2) CLI Basics

| Command                                       | What it does      | Notes                                  |
| --------------------------------------------- | ----------------- | -------------------------------------- |
| `redis-cli`                                   | Open CLI          | Defaults: 127.0.0.1:6379               |
| `redis-cli -a <password>`                     | Auth              | Avoid pasting secrets in shared shells |
| `redis-cli -h <host> -p <port> -a <password>` | Remote connect    | Use TLS if possible                    |
| `ping`                                        | Connectivity test | Should return `PONG`                   |

---

## 3) Common Key Operations

| Command                                  | What it does         | Notes                 |
| ---------------------------------------- | -------------------- | --------------------- |
| `SET user:100 "Alice"`                   | String set           |                       |
| `GET user:100`                           | Retrieve value       |                       |
| `DEL user:100`                           | Delete key           |                       |
| `HSET user:1000 name "Mohamed" age "30"` | Hash                 | Store multiple fields |
| `HGETALL user:1000`                      | Read all fields      |                       |
| `LPUSH queue job1`                       | Add to list (left)   | Queue-style           |
| `LRANGE queue 0 -1`                      | Show all list items  |                       |
| `SADD tags python fastapi`               | Add set members      | Unique collection     |
| `SMEMBERS tags`                          | Show all set members |                       |
| `ZADD scores 100 "ebrahim"`              | Sorted set           | Leaderboards          |
| `ZRANGE scores 0 -1 WITHSCORES`          | Ordered view         |                       |

---

## 4) Keys & Expiration

| Command                           | What it does           | Notes                                 |
| --------------------------------- | ---------------------- | ------------------------------------- |
| `SETEX session:123 900 "data"`    | Set with TTL (900s)    | Equivalent to `SET key value EX 900`  |
| `TTL session:123`                 | Time-to-live left      | `-1` = no TTL                         |
| `EXPIRE session:123 60`           | Add/update TTL         | Seconds                               |
| `PERSIST session:123`             | Remove TTL             | Make permanent                        |
| `SCAN 0 MATCH "user:*" COUNT 100` | Cursor-based iteration | Safer than `KEYS` in prod             |
| `KEYS "user:*"`                   | List keys              | Dev only (blocks server if many keys) |

---

## 5) Persistence Modes

| Mode              | Config                 | Notes                       |
| ----------------- | ---------------------- | --------------------------- |
| RDB (snapshot)    | `save 900 1` (default) | Saves dump.rdb on intervals |
| AOF (append-only) | `appendonly yes`       | Durable but larger          |
| Hybrid            | Both enabled           | Safer recovery              |
| Ephemeral         | Neither                | Data lost on restart        |

**Check:**

```bash
redis-cli CONFIG GET save
redis-cli CONFIG GET appendonly
```

---

## 6) Integration with FastAPI / Postgres

### Example: Repository-level caching decorator

```python
@cache(key_pattern=CacheKeys.USER, ttl=900)
def get_by_id(self, user_id: UUID) -> User:
    db_user = (self.db.query(UserModel)
              .options(joinedload(UserModel.notebooks))
              .filter(UserModel.id == user_id)
              .first())
    if not db_user:
        raise UserNotFoundException()
    return db_user.to_entity()
```

* **Flow:** Query → Redis → (if miss) Postgres → Cache result.
* **Invalidate:** On update/delete, call `invalidate(CacheKeys.USER.format(user_id=…))`.
* **TTL defaults:** 900s (15 min) — adjust per SLA.

---

## 7) Monitoring & Stats

| Command                    | What it does         | Notes                  |
| -------------------------- | -------------------- | ---------------------- |
| `redis-cli INFO`           | General info         | Memory, clients, CPU   |
| `redis-cli INFO memory`    | Memory usage         | Peak, fragmentation    |
| `redis-cli INFO stats`     | Ops per sec          | Good for load test     |
| `redis-cli MONITOR`        | Stream all ops       | Debug only (blocks)    |
| `redis-cli CLIENT LIST`    | Connected clients    | See IPs, idle times    |
| `redis-cli SLOWLOG GET 10` | Last 10 slow queries | Default threshold 10ms |

---

## 8) Docker / Compose (Redis Service)

| Command                                                      | What it does         | Notes            |
| ------------------------------------------------------------ | -------------------- | ---------------- |
| `docker compose up -d redis`                                 | Start service        |                  |
| `docker compose logs -f redis`                               | Tail logs            |                  |
| `docker compose exec redis redis-cli`                        | CLI inside container |                  |
| `docker run --rm -it redis:6.4.0 redis-cli -h redis -p 6379` | One-off client       | Use service name |

**Compose snippet with persistence:**

```yaml
services:
  redis:
    image: redis:6.4.0
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: ["redis-server", "--appendonly", "yes"]
volumes:
  redis_data:
```

---

## 9) Security (Prod)

| Area        | Action                                                     |
| ----------- | ---------------------------------------------------------- |
| Password    | Set `requirepass` or `REDIS_PASSWORD` in Compose/Cloud     |
| Bind        | Restrict with `bind 127.0.0.1` or private VPC              |
| TLS         | Use stunnel or native TLS build                            |
| Firewall    | Only allow app servers to connect                          |
| Keys        | Namespacing (`app:user:{id}`) avoids collisions            |
| Persistence | Store dumps/AOF on durable disks (cloud volume, EBS, etc.) |

---

## 10) Troubleshooting “Gotchas”

| Symptom                                     | Quick check                      | Fix                                      |
| ------------------------------------------- | -------------------------------- | ---------------------------------------- |
| Keys disappear after restart                | `CONFIG GET save` / `appendonly` | Enable RDB/AOF persistence               |
| High memory usage                           | `INFO memory`                    | Eviction policy, TTLs, maxmemory setting |
| `OOM command not allowed`                   | `CONFIG GET maxmemory`           | Increase memory or tune eviction         |
| `DENIED Redis is running in protected mode` | Running without bind/pass        | Configure `bind` and `requirepass`       |
| Constant cache misses                       | Keys mismatch                    | Check serializer/key pattern consistency |
| High CPU with MONITOR                       | Avoid using in prod              | Use `INFO` / `SLOWLOG` instead           |

---
