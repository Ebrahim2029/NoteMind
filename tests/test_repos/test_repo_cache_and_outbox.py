from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4, UUID

import types
import sys

# Patch cache.redis_client with a fake in-memory implementation
class FakeRedis:
    def __init__(self):
        self.kv: Dict[str, str] = {}
        self.deleted: List[str] = []

    def get(self, key: str) -> Optional[str]:
        return self.kv.get(key)

    def setex(self, key: str, ttl: int, val: str) -> None:
        self.kv[key] = val

    def expire(self, key: str, ttl: int) -> None:
        # no-op for tests
        pass

    def delete(self, *keys: str) -> None:
        for k in keys:
            self.kv.pop(k, None)
            self.deleted.append(k)

# Inject fake redis_client into cache_mixin via `cache` module
import infrastructure.cache as cache_mod
fake_redis = FakeRedis()
cache_mod.redis_client = fake_redis

# Capture outbox events by monkeypatching utils.outbox.emit_event
events: List[Dict[str, Any]] = []

import utils.outbox as outbox_mod
def _capture_event(ev: Dict[str, Any], stream: str = "notes:events"):
    events.append(ev)
outbox_mod.emit_event = _capture_event

# Build minimal SQLAlchemy-like stubs for session and ORM models
class FakeQuery:
    def __init__(self, data):
        self.data = data
        self._filter = None

    def filter(self, predicate):
        self._filter = predicate
        return self

    def first(self):
        # very simple matcher: predicate is a lambda over obj
        for obj in self.data:
            # The predicate is usually compiled SQLAlchemy expr; we emulate by checking id equality scenarios
            # We'll simply return the first entry.
            return obj
        return None

class FakeSession:
    def __init__(self, table: List[Any]):
        self.table = table
        self.committed = False

    def query(self, model):
        return FakeQuery(self.table)

    def add(self, obj):
        self.table.append(obj)

    def flush(self):
        pass

    def delete(self, obj):
        self.table.remove(obj)

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

# ----- Fake ORM models -----
class _UserModel:
    def __init__(self, id, username, email, is_active=True, preferences=None):
        self.id = id
        self.username = username
        self.email = email
        self.is_active = is_active
        self.preferences = preferences or {}
        self.created_at = None
        self.updated_at = None

# Monkeypatch module imports for repositories to use our fakes
sys.modules["user_models"] = types.ModuleType("user_models")
setattr(sys.modules["user_models"], "UserModel", _UserModel)

# Import repositories after monkeypatch
from core.repositories.user_repository import UserRepository
from core.entities.user import User


def test_user_repo_cache_and_outbox():
    # Start with empty table
    table: List[_UserModel] = []
    db = FakeSession(table)

    repo = UserRepository(db)

    # Create
    user = User(username="alice", email="a@example.com")
    created = repo.create(user)
    assert db.committed is True
    assert events and events[-1]["op"] == "user_create"

    # Prime "DB" object
    table.append(_UserModel(id=created.id.value, username="alice", email="a@example.com"))

    # First get -> miss → DB load and cache set
    got1 = repo.get_by_id(created.id.value)
    assert got1 is not None

    # Mutate table to prove cache is used
    table.clear()
    got2 = repo.get_by_id(created.id.value)
    assert got2 is not None  # served from cache even though table cleared

    # Update
    got2.username = "alice2"
    updated = repo.update(got2)
    assert any(ev["op"] == "user_update" for ev in events)
