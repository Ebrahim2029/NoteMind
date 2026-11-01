# tests/perf/test_repo_concurrency.py
from __future__ import annotations

import threading
import time
from statistics import mean
from typing import List
from uuid import uuid4

import pytest

from infrastructure.database import SessionLocal
from core.repositories.user_repository import UserRepository
from core.repositories.notebook_repository import NotebookRepository
from core.repositories.note_repository import NoteRepository
from core.entities.user import User
from core.entities.notebook import Notebook
from core.entities.note import Note


def _worker_latencies(
    n_ops: int,
    lat_out: List[float],
    errors: List[str],
    start_barrier: threading.Barrier,
) -> None:
    """
    Single worker function executed in a separate thread.

    What it does per worker:
      1) Opens its own DB session (one Session per thread).
      2) Creates a fresh user and a notebook.
      3) Waits at a barrier so all threads start the timed loop together.
      4) Repeats 'n_ops' times:
         - Create a note under the worker's notebook.
         - Run a simple read (filter) on that notebook.
         - Measure per-iteration wall time and record it in 'lat_out'.
    Any exception is captured as a string in 'errors' so the main test can fail.
    """
    db = SessionLocal()
    try:
        urepo = UserRepository(db)
        nbrepo = NotebookRepository(db)
        nrepo = NoteRepository(db)

        # Bootstrap per-thread user + notebook
        u = User(
            username=f"u_{uuid4().hex[:8]}",
            email=f"{uuid4().hex[:8]}@ex.com",
            preferences={},
            is_active=True,
        )
        urepo.create(u)

        nb = Notebook(user_id=u.id.value, name="Perf", color="#E3F2FD")
        nbrepo.create(nb)

        # Synchronize start with other threads to create a real concurrent burst
        start_barrier.wait()

        # Timed CRUD loop
        for _ in range(n_ops):
            n = Note(notebook_id=nb.id.value, title="t", content="c", tags=["x"])
            t0 = time.perf_counter()
            nrepo.create(n)
            nrepo.filter_notes(notebook_id=nb.id.value, tags_any=["x"], limit=10)
            t1 = time.perf_counter()
            lat_out.append(max(0.0, t1 - t0))

    except Exception as e:
        # Store the exception for the main thread to assert on
        errors.append(repr(e))
    finally:
        db.close()


@pytest.mark.usefixtures("redis_cleanup")
@pytest.mark.parametrize("threads,ops", [(5, 20), (10, 20)])
def test_repo_concurrency_smoke(threads: int, ops: int):
    """
    Smoke concurrency test.

    Parameters (as used in this test):
      - threads: number of concurrent workers (think: "concurrent users").
      - ops: number of CRUD cycles each worker performs.

    What it verifies:
      - No exceptions occurred in any thread.
      - We recorded exactly 'threads * ops' latency samples.
      - The average per-op wall time is below a loose guardrail (< 0.1 s).

    Note:
      There is no explicit "spawn rate" or "duration" here.
      All threads start together (barrier), so it's an immediate burst test.
    """
    latencies: List[float] = []
    errors: List[str] = []
    ths: List[threading.Thread] = []
    start_barrier = threading.Barrier(threads)

    # Start N threads (each will block at the barrier until all are ready)
    for _ in range(threads):
        t = threading.Thread(
            target=_worker_latencies,
            args=(ops, latencies, errors, start_barrier),
            daemon=True,
        )
        t.start()
        ths.append(t)

    # Wait for all threads to finish
    for t in ths:
        t.join()

    # If any thread reported an error, fail the test
    assert not errors, f"exceptions in threads: {errors[:1]}"

    # Sanity check on number of samples
    assert len(latencies) == threads * ops

    # Simple SLO-style bound on average latency
    avg = mean(latencies)
    assert avg < 0.1, f"avg latency too high: {avg:.4f}s"


"""
What are “users”, “duration”, and “spawn rate” here?

Users: in this test, threads == number of concurrent users (workers).
You parametrize with (5, 20) and (10, 20), so runs are with 5 users and 10 users.

Duration: there is no fixed time-based duration. Each user performs ops iterations.
Total operations per run = threads * ops (e.g., 5×20=100 ops; 10×20=200 ops).
The wall-clock duration simply ends when those operations finish.

Spawn rate: there isn’t one. Threads are created quickly and start together at the barrier.
That’s effectively a burst (instant spawn). There’s no ramp-up.

"""