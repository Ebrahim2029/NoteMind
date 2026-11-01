# README — 02. PostgreSQL Admin & Migrations

> Scope: day-to-day Postgres administration for dev/prod, psql basics, users/roles, backups & restore, performance checks, indexes, extensions, Docker/Compose, and Alembic migrations.

---

## 1) Connect & Session Basics

| Command                                                               | What it does                  | Notes                                      |
| --------------------------------------------------------------------- | ----------------------------- | ------------------------------------------ |
| `psql -h 127.0.0.1 -p 5432 -U postgres -d smart_notes`                | Connect to DB                 | Local host/port                            |
| `docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB` | Connect inside container      | Compose service name `postgres` may differ |
| `\l` / `\c smart_notes`                                               | List DBs / connect            | psql meta-commands                         |
| `\dt` / `\di` / `\dx`                                                 | Tables / Indexes / Extensions |                                            |
| `\dn` / `\du`                                                         | Schemas / Roles               |                                            |
| `\timing on`                                                          | Show query times              | Useful during tuning                       |
| `\q`                                                                  | Quit psql                     |                                            |

---

## 2) Roles, Users, Privileges

| Command                                                                                                 | What it does      | Notes                       |
| ------------------------------------------------------------------------------------------------------- | ----------------- | --------------------------- |
| `CREATE ROLE app_user LOGIN PASSWORD '***';`                                                            | Create login role | Use secrets manager in prod |
| `GRANT CONNECT ON DATABASE smart_notes TO app_user;`                                                    | Allow DB connect  |                             |
| `GRANT USAGE ON SCHEMA public TO app_user;`                                                             | Use schema        |                             |
| `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;`                      | Data DML          |                             |
| `ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;` | Future tables too | Run as owner                |
| `REVOKE ALL ON DATABASE smart_notes FROM PUBLIC;`                                                       | Harden defaults   | Optional                    |
| `ALTER USER app_user SET search_path TO public;`                                                        | Default schema    |                             |

---

## 3) Extensions You’ll Likely Need

| Command                                              | Why                                      |
| ---------------------------------------------------- | ---------------------------------------- |
| `CREATE EXTENSION IF NOT EXISTS pgcrypto;`           | `gen_random_uuid()` in models/migrations |
| `CREATE EXTENSION IF NOT EXISTS pg_stat_statements;` | Track slow/top queries (prod)            |
| `CREATE EXTENSION IF NOT EXISTS uuid-ossp;`          | Alternative UUID gen (if used)           |

**Check:**

```sql
SELECT * FROM pg_extension;
```

---

## 4) Schema & Index Management

| Command                                                                                   | What it does                         | Notes                   |
| ----------------------------------------------------------------------------------------- | ------------------------------------ | ----------------------- |
| `\d+ notes`                                                                               | Describe table with size             |                         |
| `SELECT indexname, indexdef FROM pg_indexes WHERE tablename='notes';`                     | Show indexes                         |                         |
| `CREATE INDEX CONCURRENTLY idx_notes_updated_at ON notes (updated_at);`                   | Online index build                   | Use in prod (no lock)   |
| `DROP INDEX CONCURRENTLY idx_notes_updated_at;`                                           | Online drop                          |                         |
| `CREATE UNIQUE INDEX CONCURRENTLY uq_notebooks_user_title ON notebooks (user_id, title);` | Prevent dup notebook titles per user |                         |
| `VACUUM (VERBOSE, ANALYZE);`                                                              | Reclaim + stats                      | Schedule via autovacuum |
| `ANALYZE notes;`                                                                          | Refresh stats for planner            | After bulk load         |

---

## 5) Performance & Inspection

| Command                                                                                      | What it does        | Notes                 |
| -------------------------------------------------------------------------------------------- | ------------------- | --------------------- |
| `EXPLAIN (ANALYZE, BUFFERS) SELECT ...;`                                                     | Real execution plan | Use carefully in prod |
| `SELECT * FROM pg_stat_activity WHERE datname='smart_notes';`                                | Active sessions     | See blockers          |
| `SELECT * FROM pg_locks WHERE NOT granted;`                                                  | Waiting locks       |                       |
| `SELECT * FROM pg_stat_database;`                                                            | High-level stats    |                       |
| `SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;` | Top queries by time | Requires extension    |
| `SHOW max_connections; SHOW shared_buffers;`                                                 | Config peek         |                       |
| `SELECT now(), pg_postmaster_start_time();`                                                  | Uptime              |                       |

---

## 6) Backups & Restore

### Logical (pg\_dump / pg\_restore)

| Command                                                      | What it does      | Notes                     |
| ------------------------------------------------------------ | ----------------- | ------------------------- |
| `pg_dump -h host -U user -d smart_notes -F c -f backup.dump` | Compressed dump   | Schema+data               |
| `pg_dump -h host -U user -d smart_notes -F p -f backup.sql`  | Plain SQL         | Human-readable            |
| `pg_restore -h host -U user -d smart_notes -c backup.dump`   | Restore & clean   | `-c` drops before restore |
| `psql -h host -U user -d smart_notes -f backup.sql`          | Restore plain SQL |                           |

### Dev shortcuts (Docker)

| Command                                                                                                                                                                      | What it does |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| `docker compose exec postgres pg_dump -U $POSTGRES_USER -d $POSTGRES_DB -F c -f /tmp/backup.dump`                                                                            |              |
| `docker cp $(docker compose ps -q postgres):/tmp/backup.dump ./backup.dump`                                                                                                  |              |
| `docker cp ./backup.dump $(docker compose ps -q postgres):/tmp/backup.dump && docker compose exec postgres pg_restore -U $POSTGRES_USER -d $POSTGRES_DB -c /tmp/backup.dump` |              |

> For **PITR (Point-in-Time Recovery)** use base backups + WAL archiving (e.g., `archive_mode=on`, `archive_command=…`) with tools like `pg_basebackup` or a managed service snapshot. Keep WAL on durable storage.

---

## 7) Maintenance & Housekeeping

| Task                       | Command                                                                                                                                                                           | Notes                                 |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Table bloat check (approx) | `VACUUM (ANALYZE)` / `VACUUM FULL`                                                                                                                                                | FULL locks table; avoid in prod hours |
| Reindex when needed        | `REINDEX INDEX idx_name;`                                                                                                                                                         | Use sparingly                         |
| Connection cleanup         | `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND datname='smart_notes' AND state='idle' AND now()-state_change > interval '30 minutes';` | Policy-driven                         |
| Autovacuum settings        | `ALTER TABLE notes SET (autovacuum_vacuum_scale_factor=0.1);`                                                                                                                     | Tweak per hot tables                  |

---

## 8) Migrations (Alembic) — Team Workflow

| Step           | Command                                                            | Notes                                |
| -------------- | ------------------------------------------------------------------ | ------------------------------------ |
| Generate       | `alembic revision --autogenerate -m "add idx on notes.updated_at"` | Ensure models imported in env        |
| Review         | Open the new revision file                                         | Verify ops: add/remove cols, indexes |
| Apply (dev)    | `alembic upgrade head`                                             |                                      |
| Rollback (dev) | `alembic downgrade -1`                                             |                                      |
| Check drift    | `alembic current` / `alembic history`                              |                                      |
| Stamp (sync)   | `alembic stamp head`                                               | Align without running (careful)      |

**CI tip:** Run `alembic upgrade head` against a fresh test DB to catch missing migrations.

---

## 9) Docker / Compose (Postgres Service)

| Command                                                               | What it does | Notes                   |
| --------------------------------------------------------------------- | ------------ | ----------------------- |
| `docker compose up -d postgres`                                       | Start DB     |                         |
| `docker compose logs -f postgres`                                     | Tail logs    |                         |
| `docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB` | psql shell   |                         |
| `docker stats`                                                        | Live metrics | Handy during load tests |

**Healthcheck (compose snippet)**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: smart_notes
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 10s
      timeout: 5s
      retries: 5
```

---

## 10) Connection Pooling (PgBouncer) — Optional but Recommended in Prod

| Command                          | What it does                   | Notes                                          |
| -------------------------------- | ------------------------------ | ---------------------------------------------- |
| `docker compose up -d pgbouncer` | Start pooler                   | Configure `DATABASE_URL` to point at PgBouncer |
| Mode                             | `transaction` mode             | Good default for app workloads                 |
| Env                              | `POOL_SIZE`, `MAX_CLIENT_CONN` | Tune for API concurrency                       |

---

## 11) Security & Compliance Quickies

| Area     | Action                                                         |
| -------- | -------------------------------------------------------------- |
| Network  | Bind Postgres to private network / security group only         |
| TLS      | Use TLS for external connections (or private VPC only)         |
| Secrets  | Never hardcode passwords—use env/secret manager                |
| Backups  | Automate daily dumps + retain (e.g., 7/30/90 rotation)         |
| Auditing | Enable `log_connections`, `log_disconnections`, slow query log |

---

## 12) Common “Gotchas”

| Symptom                                     | Quick check                      | Fix                                               |
| ------------------------------------------- | -------------------------------- | ------------------------------------------------- |
| `function gen_random_uuid() does not exist` | `\dx`                            | `CREATE EXTENSION pgcrypto;`                      |
| Autogenerate misses changes                 | Alembic env not importing models | Ensure models imported and metadata bound         |
| Slow text search                            | Missing GIN index on `tsvector`  | Create GIN/GIST indexes for search fields         |
| Deadlocks under load                        | Lock graph                       | Reduce transaction scope; consistent update order |
| CPU spikes                                  | `pg_stat_statements` top queries | Add indexes; reduce N+1; batch writes             |
| Connection storms                           | Too many app workers             | Add PgBouncer; tune SQLAlchemy pool               |

---

### Solution: Connect Both Containers to the Same Network

1. **First, verify if the network exists:**
   ```bash
   docker network ls | grep smart_notes_network
   ```

2. **If the network doesn't exist, create it:**
   ```bash
   docker network create smart_notes_network
   ```

3. **Connect your PostgreSQL container to the network:**
   ```bash
   docker network connect smart_notes_network postgres_note_main
   ```

4. **Connect your pgAdmin container to the network:**
   ```bash
   docker network connect smart_notes_network smart_notes_pgadmin
   ```

5. **Verify both containers are now on the network:**
   ```bash
   docker inspect postgres_note_main | grep -A 5 Networks
   docker inspect smart_notes_pgadmin | grep -A 5 Networks
   ```

6. **Test the connection in pgAdmin:**
   - Access pgAdmin at http://localhost:5050
   - When adding a new server, use:
     - Host name/address: `postgres_note_main`
     - Port: `5432`
     - Username: Your PostgreSQL username (default is usually `postgres`)
     - Password: Your PostgreSQL password

### Important Notes:
- The container name (`postgres_note_main`) becomes the hostname within Docker's network
- No need to expose PostgreSQL ports to your host machine
- This solution works without stopping your existing containers
- For persistence, consider adding these containers to a docker-compose.yml file in the future

### Troubleshooting:
If you still can't connect:
1. Check PostgreSQL logs:
   ```bash
   docker logs postgres_note_main
   ```
2. Test connectivity from pgAdmin container:
   ```bash
   docker exec -it smart_notes_pgadmin ping postgres_note_main
   ```


---

### Solution: Connect Containers to the Correct Network

1. **Connect your PostgreSQL container:**
```bash
docker network connect note_mind_smart_notes_network postgres_note_main
```

2. **Connect your pgAdmin container:**
```bash
docker network connect note_mind_smart_notes_network smart_notes_pgadmin
```

3. **Verify the connections:**
```bash
docker inspect postgres_note_main | grep -A 5 Networks
docker inspect smart_notes_pgadmin | grep -A 5 Networks
```

### Why This Works:
- Docker Compose automatically prefixes network names with your project folder name (Note_Mind → note_mind)
- The full network name is `note_mind_smart_notes_network`
- Both containers need to be on this exact same network to communicate

### Connecting in pgAdmin:
Now you can connect to PostgreSQL from pgAdmin using:
- **Hostname:** `postgres_note_main`
- **Port:** `5432`
- **Username/Password:** As configured in your PostgreSQL container

### Pro Tip:
To avoid this confusion in the future, you can either:
1. Use the same network name consistently, or
2. Let Docker Compose manage all your containers together

Would you like me to show you how to check which containers are already connected to this network?