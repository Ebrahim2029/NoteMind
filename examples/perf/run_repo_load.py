# examples/perf/run_repo_load.py

import logging
 # Keep your app logs, quiet SQLAlchemy’s chatter
for name in ("sqlalchemy", "sqlalchemy.engine", "sqlalchemy.pool", "sqlalchemy.orm", "sqlalchemy.dialects"):
        lg = logging.getLogger(name)
        lg.setLevel(logging.WARNING)      # or logging.ERROR to be stricter
        lg.propagate = False              # don't bubble to root handlers
import argparse
import collections
import random
import string
import threading
import time
from functools import partial
from dataclasses import dataclass
from statistics import median
from typing import Callable, Dict, List, Tuple
from uuid import uuid4
import traceback

from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

# DB
from infrastructure.database import SessionLocal, Base, engine
from app_config import app_settings

# Repositories
from core.repositories.user_repository import UserRepository
from core.repositories.notebook_repository import NotebookRepository
from core.repositories.note_repository import NoteRepository

# Domain entities (+ value objects for explicit IDs)
from core.entities.user import User
from core.entities.notebook import Notebook
from core.entities.note import Note
from core.entities.value_objects.user_id import UserId
from core.entities.value_objects.notebook_id import NotebookId
from core.entities.value_objects.note_id import NoteId

from utils.clean_data import cleanup_database
# Optional resource monitor (fallback to no-op if missing)
try:
    from utils.profiling.resource_monitor import ResourceMonitor
except Exception:
    class ResourceMonitor:
        def __init__(self, interval_sec=1.0, out_csv_path="metrics.csv"): pass
        def start(self): pass
        def stop(self): pass


import secrets
from faker import Faker
faker = Faker()

def _uniq_suffix(n=3):  # 6 hex chars
    return secrets.token_hex(n)



# Ensure schema
Base.metadata.create_all(bind=engine)

RETRIABLE_SNIPPETS = ("deadlock detected", "could not serialize access")
ROLLBACK_ERRORS_FILE = "examples/perf/rollback_errors.log"
rollback_errors: List[dict] = []
ERR_SAMPLES = 0

@dataclass
class LatencyMetric:
    op: str
    ok: bool
    dur_ms: float

class Worker(threading.Thread):
    def __init__(self, name: str, stop_event: threading.Event, results: List[LatencyMetric]):
        super().__init__(name=name, daemon=True)
        self.stop_event = stop_event
        self.results = results

    def run(self):
        db = SessionLocal()
        try:
            user_repo = UserRepository(db)
            nb_repo = NotebookRepository(db)
            note_repo = NoteRepository(db)

            # Bootstrap user with explicit ID
            u = User(
                id=UserId(str(uuid4())),
                username=faker.user_name(),
                email=f"{_uniq_suffix(12)}@load.example",
                preferences={},
                is_active=True,
            )
            # Option B: partial (clean and safe in loops)
            _timed(self.results, "user.create", lambda: _with_retry(partial(user_repo.create, u)))

            # Bootstrap notebook with explicit ID
            nb = Notebook(
                id=NotebookId(str(uuid4())),
                user_id=u.id.value,
                name=_rand("Work_"),
                color="#E3F2FD",
            )
            _timed(self.results, "nb.create",   lambda: _with_retry(partial(nb_repo.create, nb)))

            # Main loop
            while not self.stop_event.is_set():
                ops: List[Tuple[str, Callable[[], None]]] = [
                    ("note.create", lambda: _note_create(note_repo, nb.id.value)),
                    ("note.filter.tags_any", lambda: _note_filter_tags_any(note_repo, nb.id.value)),
                    ("note.update", lambda: _note_update_random(note_repo, nb.id.value)),
                    ("user.get_by_email", lambda: user_repo.get_by_email(u.email)),
                    ("nb.get_by_user", lambda: nb_repo.get_by_user(u.id.value)),
                ]
                weights = [2, 3, 2, 4, 3]  # ~70% reads
                op_name, fn = random.choices(ops, weights=weights, k=1)[0]
                _timed(self.results, op_name, fn)
        finally:
            db.close()

def _with_retry(fn, attempts=3):
    for i in range(attempts):
        try:
            return fn()
        except OperationalError as e:
            msg = str(e).lower()
            if any(s in msg for s in RETRIABLE_SNIPPETS) and i < attempts - 1:
                time.sleep(0.05 * (2 ** i) + random.random() * 0.03)
                continue
            raise

def _note_create(note_repo: NoteRepository, notebook_id) -> None:
    tags_pool = ["x", "y", "z", "todo", "idea", "urgent"]
    n = Note(
        id=NoteId(str(uuid4())),
        notebook_id=notebook_id,
        title=faker.sentence(nb_words=4),
        content=faker.paragraph(nb_sentences=7),
        tags=random.sample(tags_pool, k=random.randint(1, 3)),
        color=faker.hex_color(),
        attachments=[],
        is_pinned=False,
        is_archived=False,
        is_deleted=False,
        reminder=None,
    )
    _with_retry(lambda: note_repo.create(n))

def _note_filter_tags_any(note_repo: NoteRepository, notebook_id) -> None:
    _ = note_repo.filter_notes(notebook_id=notebook_id, tags_any=["z"], limit=20)

def _note_update_random(note_repo: NoteRepository, notebook_id) -> None:
    notes = note_repo.filter_notes(notebook_id=notebook_id, limit=5)
    if not notes:
        return
    n = random.choice(notes)
    n.title = faker.sentence(nb_words=5)
    n.tags = list(set((n.tags or []) + [random.choice(["x", "y", "z"])]))
    if notes:
        _with_retry(lambda: note_repo.update(n))

def _rand(prefix: str, n: int = 12) -> str:
    return prefix + "".join(random.choice(string.ascii_lowercase) for _ in range(n))

def _log_rollback_errors():
    if not rollback_errors:
        return
    with open(ROLLBACK_ERRORS_FILE, "w") as f:
        f.write("=== Rollback Errors Log ===\n")
        f.write(f"Total rollback errors: {len(rollback_errors)}\n\n")
        for i, error in enumerate(rollback_errors, 1):
            f.write(f"Error #{i}:\n")
            f.write(f"Operation: {error['op']}\n")
            f.write(f"Timestamp: {error['timestamp']}\n")
            f.write(f"Error:\n{error['traceback']}\n")
            f.write("-" * 50 + "\n")

def _timed(results, op, fn):
    global ERR_SAMPLES, rollback_errors
    t0 = time.perf_counter()
    ok = True
    try:
        fn()
    except (IntegrityError, SQLAlchemyError, Exception) as e:
        ok = False
        tb = traceback.format_exc()
        if "ROLLBACK" in str(e).upper() or "ROLLBACK" in tb:
            rollback_errors.append({
                'op': op,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'traceback': tb
            })
        if ERR_SAMPLES < 3:
            ERR_SAMPLES += 1
            print("\n--- ERROR SAMPLE ---------------------------------")
            print(tb)
            print("--------------------------------------------------\n")
    finally:
        results.append(LatencyMetric(op=op, ok=ok, dur_ms=(time.perf_counter() - t0) * 1000))

def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return s[k]

def _summarize(results: List[LatencyMetric]) -> None:
    by_op: Dict[str, List[LatencyMetric]] = collections.defaultdict(list)
    for r in results:
        by_op[r.op].append(r)

    print("\n=== Summary ===")
    total = len(results)
    ok = sum(1 for r in results if r.ok)
    print(f"Total ops: {total} | OK: {ok} | Errors: {total - ok} | Success rate: {ok/total:.2%}")

    for op, arr in sorted(by_op.items()):
        lat = [r.dur_ms for r in arr if r.ok]
        if not lat:
            print(f"{op:22s} - no successful samples")
            continue
        p50 = median(lat)
        p95 = _percentile(lat, 95)
        p99 = _percentile(lat, 99)
        print(f"{op:22s} n={len(arr):5d} | p50={p50:7.2f} ms | p95={p95:7.2f} ms | p99={p99:7.2f} ms")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=50)
    parser.add_argument("--spawn-rate", type=float, default=10.0)
    parser.add_argument("--duration", type=int, default=30)
    parser.add_argument("--metrics-out", type=str, default="examples/perf/metrics.csv")
    args = parser.parse_args()

    print(f"DB: {app_settings.POSTGRES_HOST}/{app_settings.POSTGRES_DB} | Redis: {app_settings.REDIS_HOST}")
    results: List[LatencyMetric] = []

    stop = threading.Event()
    monitor = ResourceMonitor(interval_sec=0.5, out_csv_path=args.metrics_out)
    monitor.start()

    workers: List[Worker] = []
    t_end = time.perf_counter() + args.duration

    try:
        for i in range(args.users):
            if time.perf_counter() >= t_end:
                break
            w = Worker(name=f"W{i+1}", stop_event=stop, results=results)
            w.start()
            workers.append(w)
            time.sleep(1.0 / max(1e-6, args.spawn_rate))

        while time.perf_counter() < t_end:
            time.sleep(0.25)
    finally:
        stop.set()
        for w in workers:
            w.join()
        monitor.stop()
        _log_rollback_errors()

    _summarize(results)
    print(f"Rollback errors logged: {len(rollback_errors)}")

if __name__ == "__main__":
    cleanup_database()
    main()
