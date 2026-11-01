# README — 05. Chroma / Vector DB Ops

> Scope: Using **ChromaDB** (vector database) with FastAPI, Docker, and Python. Covers setup, schema concepts, queries, persistence, monitoring, and troubleshooting.

---

## 1) Service Management (Docker / Compose)

| Command                                             | What it does             | Notes                        |
| --------------------------------------------------- | ------------------------ | ---------------------------- |
| `docker run -d -p 8001:8000 chromadb/chroma:latest` | Run standalone Chroma    | Maps to host port 8001       |
| `docker compose up -d chroma`                       | Start service from stack | With persistence (see below) |
| `docker compose logs -f chroma`                     | Tail logs                | Debug startup / API calls    |
| `docker compose exec chroma bash`                   | Exec into container      | Inspect `/chroma` storage    |

**Compose snippet with persistence:**

```yaml
chroma:
  image: chromadb/chroma:latest
  ports:
    - "8001:8000"
  volumes:
    - chroma_data:/chroma
volumes:
  chroma_data:
```

---

## 2) Python Client Setup

```bash
pip install chromadb
```

**Basic usage:**

```python
import chromadb

client = chromadb.HttpClient(host="localhost", port=8001)
collection = client.get_or_create_collection("notes")

# Insert embeddings
collection.add(
    ids=["note1"],
    documents=["FastAPI is great for async APIs"],
    metadatas=[{"user": "123"}]
)

# Query
results = collection.query(
    query_texts=["What framework is good for async APIs?"],
    n_results=3
)
print(results)
```

---

## 3) Core Concepts

| Concept        | Description                         | Example                              |
| -------------- | ----------------------------------- | ------------------------------------ |
| **Collection** | Logical grouping of vectors         | `"notes"`, `"articles"`              |
| **Document**   | Raw text stored alongside embedding | `"FastAPI guide"`                    |
| **Embedding**  | Vector representation of doc/query  | Generated via OpenAI API             |
| **Metadata**   | Key/value tags                      | `{"user": "123", "topic": "python"}` |
| **ID**         | Unique identifier                   | `"note_123"`                         |

---

## 4) Example Workflows

### Insert batch of notes

```python
collection.add(
    ids=["n1","n2"],
    documents=["Redis caching guide", "Postgres index tuning"],
    metadatas=[{"topic":"redis"}, {"topic":"postgres"}]
)
```

### Semantic search

```python
collection.query(
    query_texts=["how to cache queries"],
    where={"topic": "redis"},
    n_results=5
)
```

### Delete by ID

```python
collection.delete(ids=["n1"])
```

---

## 5) Persistence & Storage

* Default: stores data in **DuckDB** inside container (`/chroma`).
* Persist across restarts: mount a volume:

  ```yaml
  volumes:
    - ./chroma_data:/chroma
  ```
* Backup: copy directory `chroma_data/`.

---

## 6) Integration with FastAPI & Postgres

**Flow:**

1. User saves a note → stored in Postgres.
2. Same note text → embedded via OpenAI → stored in Chroma.
3. Cache high-frequency queries in Redis.
4. AI assistant → query Chroma for semantic recall → combine with Postgres metadata.

**Sync pattern (Observer):**

* On `note.create` → add to Postgres + Chroma.
* On `note.update` → update both.
* On `note.delete` → remove from both.

---

## 7) Health & Monitoring

| Command                                       | What it does                        |
| --------------------------------------------- | ----------------------------------- |
| `curl http://localhost:8001/api/v1/heartbeat` | Simple heartbeat check              |
| `docker compose logs -f chroma`               | Watch queries arriving              |
| `du -sh chroma_data/`                         | Check storage size                  |
| `iotop` / `htop`                              | Monitor disk/CPU if heavy workloads |

---

## 8) Performance Tips

* Use **batch insert** (`collection.add` with lists) instead of single inserts.
* Keep embeddings **consistent dimension** (same model across collection).
* Partition collections logically (e.g., per user, per domain).
* Use `where` filters (metadata) to narrow search before vector similarity.
* Periodically **compact DuckDB** (via DuckDB tools) if size grows.

---

## 9) Security (Prod)

| Area    | Action                                                        |
| ------- | ------------------------------------------------------------- |
| Network | Run Chroma behind private network or reverse proxy            |
| Auth    | Protect with API gateway (Chroma itself doesn’t enforce auth) |
| Volumes | Use encrypted volumes if sensitive notes                      |
| Backups | Automate snapshots of `chroma_data`                           |

---

## 10) Troubleshooting “Gotchas”

| Symptom                  | Quick check                     | Fix                              |
| ------------------------ | ------------------------------- | -------------------------------- |
| Data gone after restart  | Was volume mounted?             | Add persistent volume            |
| Queries super slow       | Too many docs in one collection | Partition by topic/user          |
| Embedding errors         | Mismatch in vector dims         | Ensure same embedding model used |
| API `Connection refused` | Port exposed? Service healthy?  | Check `docker compose ps`        |
| High disk growth         | Many deletes but no vacuum      | Rebuild/compact DuckDB           |

---

