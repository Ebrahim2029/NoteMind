# README — 06. FastAPI Ops (Run, Debug, Gunicorn/Uvicorn workers)

> Scope: Running and managing **FastAPI** in dev/prod. Includes local dev commands, debugging, hot reload, ASGI workers (Gunicorn + Uvicorn), logging, profiling, and healthchecks.

---

## 1) Local Development (uvicorn)

| Command                                           | What it does             | Notes                   |
| ------------------------------------------------- | ------------------------ | ----------------------- |
| `uvicorn app.main:app --reload --port 8000`       | Run with hot reload      | Dev only                |
| `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Listen on all interfaces | Needed inside Docker/VM |
| `APP_ENV=dev uvicorn app.main:app`                | Run with env flag        | Ensure config reads env |
| `uvicorn app.main:app --reload --log-level debug` | Extra logs               | Debugging routes        |

---

## 2) Gunicorn + Uvicorn Workers (Production)

| Command                                                                       | What it does         | Notes                 |
| ----------------------------------------------------------------------------- | -------------------- | --------------------- |
| `gunicorn -k uvicorn.workers.UvicornWorker app.main:app -w 4 -b 0.0.0.0:8000` | Start with 4 workers | Common prod setup     |
| `gunicorn -k uvicorn.workers.UvicornWorker app.main:app --threads 4 -w 2`     | Threaded workers     | For mixed IO/CPU      |
| `gunicorn -k uvicorn.workers.UvicornWorker app.main:app --timeout 60`         | Set worker timeout   | Avoid long-hang kills |
| `gunicorn --reload -k uvicorn.workers.UvicornWorker app.main:app`             | Auto-reload          | For staging/dev       |

**Scaling tip:**

* `w = 2 × CPU cores + 1` is a common rule of thumb.
* Measure real-world latency and memory.

---

## 3) Docker Entrypoint Example

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

# For dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# For prod (override in docker-compose or k8s manifest)
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "-w", "4", "-b", "0.0.0.0:8000"]
```

---

## 4) Healthchecks & Readiness

**In FastAPI (app/main.py):**

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
```

**Check with curl:**

```bash
curl http://localhost:8000/health
```

**Compose healthcheck:**

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 10s
  timeout: 3s
  retries: 5
```

---

## 5) Logging & Debugging

| Command                                      | What it does        |
| -------------------------------------------- | ------------------- |
| `uvicorn app.main:app --log-level info`      | Default logs        |
| `uvicorn app.main:app --log-level debug`     | Verbose logs        |
| `uvicorn app.main:app --reload --use-colors` | Colorized logs      |
| `gunicorn --log-level warning …`             | Restrict noisy logs |

**In code:**

```python
import logging
logger = logging.getLogger("note_mind")
logger.info("User created %s", user.id)
```

---

## 6) Profiling & Performance

| Tool                                               | Command                     | Notes                    |
| -------------------------------------------------- | --------------------------- | ------------------------ |
| `pip install pytest-benchmark`                     | Benchmarks in pytest        | `@pytest.mark.benchmark` |
| `python -m cProfile -o out.prof -m app.main`       | Profile run                 | Analyze with `snakeviz`  |
| `ab -n 1000 -c 50 http://127.0.0.1:8000/notes`     | ApacheBench quick load test | For local endpoints      |
| `wrk -t4 -c100 -d30s http://127.0.0.1:8000/health` | More powerful benchmark     | Install `wrk`            |

---

## 7) Middleware & Observability

**Add CORS / Timing / GZip:**

```python
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
```

**Request logging middleware:**

```python
@app.middleware("http")
async def log_requests(request, call_next):
    from time import time
    start = time()
    response = await call_next(request)
    duration = time() - start
    print(f"{request.method} {request.url} completed in {duration:.2f}s")
    return response
```

---

## 8) Async Worker Tuning

* **DB connections:** Match pool size with Gunicorn worker count.
* **Redis clients:** Use connection pools.
* **Event loop policy:** On Linux, Uvicorn auto-uses `uvloop` (faster).
* **Max requests per worker:** Restart workers periodically to avoid leaks:

  ```bash
  gunicorn … --max-requests 1000 --max-requests-jitter 100
  ```

---

## 9) Security (Prod)

| Area           | Action                                                |
| -------------- | ----------------------------------------------------- |
| TLS            | Terminate TLS at reverse proxy (NGINX/Traefik)        |
| Headers        | Add `Secure`, `SameSite`, `Strict-Transport-Security` |
| CORS           | Restrict allowed origins in prod                      |
| Error handling | Hide stacktraces from clients                         |
| Rate limiting  | Use middleware (e.g., `slowapi`)                      |
| Auth           | JWT/OAuth2 middleware with `fastapi.security`         |

---

## 10) Troubleshooting “Gotchas”

| Symptom                         | Quick check                | Fix                                       |
| ------------------------------- | -------------------------- | ----------------------------------------- |
| API works in dev but not Docker | `docker compose logs api`  | Expose host `0.0.0.0` not `127.0.0.1`     |
| Gunicorn workers crash          | Logs show “worker failed”  | Increase timeout, check DB pool           |
| High CPU usage                  | Profiling shows sync calls | Ensure async DB driver (asyncpg)          |
| Requests hang under load        | Too few workers            | Increase `-w`, check Redis/DB bottlenecks |
| Reload not working              | Mounted volume?            | Add `-v .:/app` in compose                |

---

