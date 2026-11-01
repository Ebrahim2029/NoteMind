# README — 01. Local Development & Testing (Python / FastAPI)

> Scope: day-to-day dev workflow—run the API, manage env vars, tests, coverage, DB migrations, local Postgres/Redis access, and quick performance checks.

---

## 1) Environment Variables (quick ways)

| Command                                                         | What it does                        | Notes                      |
| --------------------------------------------------------------- | ----------------------------------- | -------------------------- |
| `APP_ENV=testing APP_DEBUG=True pytest tests/`                  | Sets env vars only for this command | POSIX shells (Linux/macOS) | 
| `env APP_ENV=testing APP_DEBUG=True pytest tests/`              | Same as above via `env`             | POSIX shells    | 
| `export $(grep -v '^#' .env.test \| xargs) && pytest`            | Load from a file then run  | Keep `.env.test` in repo (no secrets) |
| `pip install pytest-env` + `pytest.ini` `env = APP_ENV=testing` | Persistent test env via plugin      | Great for CI/local parity  |

---

## 2) Run the API (FastAPI/uvicorn)

| Command                                           | What it does                | Notes                                       |
| ------------------------------------------------- | --------------------------- | ------------------------------------------- |
| `uvicorn app.main:app --reload --port 8000`       | Dev server with auto-reload | Replace `app.main:app` with your entrypoint |
| `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Listen on all interfaces    | Useful inside Docker/VM                     |
| `APP_ENV=local uvicorn app.main:app`              | Run with env flag           | Ensure your settings read `APP_ENV`         |

---

## 3) Tests & Coverage (pytest)

| Command                                     | What it does                  | Notes                                      |
| ------------------------------------------- | ----------------------------- | ------------------------------------------ |
| `pytest`                                    | Run all tests                 | Default discovery                          |
| `pytest -k "user and not slow"`             | Filter by expression          | Include/exclude patterns                   |
| `pytest -m "integration"`                   | Run by marker                 | Mark tests with `@pytest.mark.integration` |
| `pytest -q`                                 | Quiet output                  | Cleaner logs                               |
| `pytest -x`                                 | Stop at first failure         | Fast feedback                              |
| `pytest --maxfail=3`                        | Fail fast after N failures    | Useful in CI                               |
| `pytest --cov=core --cov-branch`            | Coverage with branch analysis | Adjust package path                        |
| `pytest --cov=core --cov-report=html`       | HTML report                   | Opens at `htmlcov/index.html`              |
| `pytest --cov=core --cov-report=html tests/`| HTML report                   | Opens at `open htmlcov/index.html`         |
|`pytest --cov=core --cov-report=html tests/-k "not test_repo_concurrency.py and not test_another_file.py"`| HTML report  | Opens at `open htmlcov/index.html`|
| `pytest -n auto`                            | Parallel via xdist            | `pip install pytest-xdist`                 |
| `APP_ENV=testing pytest tests/unit/models/` | Run a subfolder               | With ephemeral env                         |
|`APP_ENV=testing APP_DEBUG=True pytest tests/test_repositories/` |Run a subfolder |With ephemeral env |

```bash
open htmlcov/index.html         # macOS
xdg-open htmlcov/index.html     # Linux
```
#### Via `.env.test` file (if you have app\_settings read from `.env`)

##### Make a file `.env.test`:

```text
APP_ENV=testing
APP_DEBUG=True
```
##### Then before running the tests:

```bash
export $(cat .env.test | xargs) && pytest tests/test_repositories/
```
---

## 4) Database Migrations (Alembic)

| Command                                  | What it does                   | Notes                       |
| ---------------------------------------- | ------------------------------ | --------------------------- |
| `alembic upgrade head`                   | Apply all migrations           | Use after pulling changes   |
| `alembic downgrade -1`                   | Revert last migration          | Careful: data loss possible |
| `alembic revision -m "add notes index"`  | Create empty revision          | For manual edits            |
| `alembic revision --autogenerate -m "…"` | Auto-generate migration        | Ensure models synced        |
| `alembic current`                        | Show current DB revision       | Debug drift                 |
| `alembic history --verbose`              | Show migration history         | With details                |
| `alembic stamp head`                     | Mark as up-to-date w/o running | For aligning clean DBs      |

---

## 5) Local Postgres (Docker Compose)

| Command                                                                                                             | What it does              | Notes                      |
| ------------------------------------------------------------------------------------------------------------------- | ------------------------- | -------------------------- |
| `docker compose ps`                                                                                                 | List services             | Find DB service name       |
| `docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB`                                               | Open psql in container    | Replace service if needed  |
| `docker exec -it <pg-container> psql -U postgres -d smart_notes`                                                    | `psql` in known container | Use `docker ps` to find it |
| `docker run --rm -it --network <compose_net> postgres:16-alpine psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB` | One-off client container  | Replace network and host   |

**Useful psql snippets:**

```sql
\l                      -- list databases
\c smart_notes          -- connect
\dt                     -- list tables
\di                     -- list indexes
\dx                     -- list extensions
SELECT indexname, indexdef FROM pg_indexes WHERE tablename='notes';
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- for gen_random_uuid()
```

---

## 6) Local Redis (service & CLI)

| Command                                        | What it does         | Notes                           |                 |   |
| ---------------------------------------------- | -------------------- | ------------------------------- | --------------- | - |
| `sudo systemctl status redis`                  | Check service status | Systemd hosts                   |                 |   |
| \`sudo systemctl start                         | stop                 | restart redis\`                 | Control service |   |
| \`sudo systemctl enable                        | disable redis\`      | Enable at boot                  |                 |   |
| `sudo journalctl -u redis -f --since=1h`       | Tail logs            | Add `--until` if needed         |                 |   |
| `sudo lsof -i :6379`                           | Check port usage     | Troubleshoot conflicts          |                 |   |
| `redis-cli`                                    | Open CLI             |                                 |                 |   |
| `redis-cli -a <password> -h 127.0.0.1 -p 6379` | CLI with auth        | Avoid pasting secrets in shells |                 |   |

---

## 7) Caching & Keys (quick checks)

| Command                                      | What it does         | Notes                       |
| -------------------------------------------- | -------------------- | --------------------------- |
| `redis-cli KEYS "user:*"`                    | List keys (dev only) | Prefer `SCAN` in prod       |
| `redis-cli SCAN 0 MATCH "cache:*" COUNT 100` | Cursor-based scan    | Safer for big keyspaces     |
| `redis-cli GET "cache:user:123"`             | Inspect value        | For debugging               |
| `redis-cli TTL "cache:user:123"`             | Check TTL            | Useful with `@cache(ttl=…)` |
| `redis-cli FLUSHALL`                         | Clear all keys       | **Danger** (dev only)       |

---

## 8) Performance / Load Smoke (Repository layer)

| Command                                                                          | What it does       | Notes             |
| -------------------------------------------------------------------------------- | ------------------ | ----------------- |
| `python -m examples.perf.run_repo_load --users 5 --spawn-rate 5 --duration 10`   | Quick local smoke  | Fast sanity check |
| `python -m examples.perf.run_repo_load --users 20 --spawn-rate 10 --duration 20` | Moderate load      |                   |
| `python -m examples.perf.run_repo_load --users 50 --spawn-rate 10 --duration 30` | Heavier local push | Monitor CPU/RAM   |

**Tips**

* Reduce SQLAlchemy logging noise in the script (already handled).
* Ensure each worker has its own Session.
* Watch `examples/perf/metrics.csv` if your script writes it.

---

## 9) Lint, Format, Types (recommended)

| Command                             | What it does | Notes                         |
| ----------------------------------- | ------------ | ----------------------------- |
| `pip install ruff black isort mypy` | Tooling      | Pin in `requirements-dev.txt` |
| `ruff check .`                      | Lint         | Fast                          |
| `black .`                           | Format       | Opinionated                   |
| `isort .`                           | Sort imports | Keep import style consistent  |
| `mypy .`                            | Static types | Configure `mypy.ini` for libs |

---

## 10) Docker & Compose (dev helpers)

| Command                                          | What it does           | Notes                      |
| ------------------------------------------------ | ---------------------- | -------------------------- |
| `docker build -t note_mind:dev .`                | Build image            | Add `--no-cache` to force  |
| `docker run -it --rm -p 8000:8000 note_mind:dev` | Run container          | Map ports                  |
| `docker compose up -d`                           | Start stack            | Daemon mode                |
| `docker compose down`                            | Stop & remove          | Add `-v` to remove volumes |
| `docker compose logs -f api`                     | Tail service logs      | Replace `api` with service |
| `docker compose exec api bash`                   | Shell into service     | Useful for debugging       |
| `docker stats`                                   | Live container metrics | CPU/RAM quick glance       |

---

## 11) Common “Gotchas”

| Symptom                             | Quick check                   | Fix                                                                     |
| ----------------------------------- | ----------------------------- | ----------------------------------------------------------------------- |
| Coverage HTML empty                 | Ran in different path         | Use project root; ensure `--cov=<package>` points to actual module path |
| Alembic autogenerate misses changes | Imports not loaded            | Ensure models are imported in Alembic env                               |
| `gen_random_uuid()` missing         | Extension not present         | `CREATE EXTENSION IF NOT EXISTS pgcrypto;`                              |
| Redis keys never expire             | Decorator TTL not set         | Confirm `@cache(ttl=900)` and that `SETEX`/`EX` is used                 |
| Same error rate under higher load   | Pooling or unique constraints | Check DB pool size, contention, unique indexes, retry strategy          |

---

