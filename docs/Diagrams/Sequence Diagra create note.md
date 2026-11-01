### 🔎 Flow Walkthrough (Create Note)

1. **Client → FastAPI (notes.py)**
   User calls `POST /api/v1/notes` with note data.

2. **FastAPI → NoteRepository (note\_repository.py)**
   `create_note()` builds a `Note` entity → calls `NoteRepository.create()`.

3. **NoteRepository → Database (PostgreSQL)**
   Persists the note inside a transaction.
   Then invalidates cache and **emits event** (`op=create`) via `emit_event()`.

4. **NoteRepository → Outbox (outbox.py)**
   `emit_event()` publishes the event to **Redis Stream (`notes:events`)**.

5. **Sync Worker (sync\_worker.py)**
   Separate worker process reads `notes:events` from Redis Stream.
   Calls `SyncService.handle(event)`.

6. **SyncService (sync\_service.py)**

   * If `op=create`: generates embedding with `embed_client`.
   * Calls `ChromaClient.upsert()` to store vector in Chroma.
   * Invalidates related Redis cache patterns.

7. **ChromaClient (chroma\_client.py)**
   Sends HTTP request to ChromaDB to upsert note vector.

---

### 📊 Sequence Diagram (Mermaid)

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI (notes.py)
    participant Repo as NoteRepository
    participant DB as PostgreSQL
    participant Cache as Redis (cache.py)
    participant Outbox as Redis Stream (outbox.py)
    participant Worker as SyncWorker
    participant Sync as SyncService
    participant Embed as EmbedClient
    participant Chroma as ChromaDB

    U->>API: POST /api/v1/notes (NoteCreate)
    API->>Repo: create(Note)
    Repo->>DB: INSERT Note
    DB-->>Repo: Note persisted
    Repo->>Cache: Invalidate CacheKeys.NOTE_BY_ID
    Repo->>Outbox: emit_event({op:create, note_id,...})
    Outbox-->>Redis: XADD notes:events

    Worker->>Redis: XREADGROUP notes:events
    Redis-->>Worker: Deliver "create" event
    Worker->>Sync: handle(event)

    Sync->>Embed: embed(title + content)
    Embed-->>Sync: vector embedding
    Sync->>Chroma: upsert(note_id, embedding, metadata)
    Chroma-->>Sync: ack
    Sync->>Cache: Invalidate patterns
```

---

