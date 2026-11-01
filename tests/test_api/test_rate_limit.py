from __future__ import annotations

import os
from typing import Dict

from fastapi import FastAPI
from fastapi.testclient import TestClient

from utils.rate_limit import RateLimitMiddleware
from utils.security import create_access_token


class _FakeRedis:
    """Simple in-memory Redis stub with minimal methods used by middleware."""
    def __init__(self):
        self.kv: Dict[str, int] = {}
        self.ttl: Dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.kv[key] = self.kv.get(key, 0) + 1
        return self.kv[key]

    def expire(self, key: str, seconds: int) -> None:
        self.ttl[key] = seconds


def _app_with_limit(limit: int, fake_redis) -> TestClient:
    # Patch middleware's redis_client reference
    import utils.rate_limit as rl
    rl.redis_client = fake_redis

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limit_per_minute=limit)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/echo")
    def echo():
        return {"ok": True}

    return TestClient(app)


def test_rate_limit_by_ip():
    client = _app_with_limit(3, _FakeRedis())

    # Simulate a client IP via X-Forwarded-For
    headers = {"X-Forwarded-For": "1.2.3.4"}
    for _ in range(3):
        r = client.get("/echo", headers=headers)
        assert r.status_code == 200, r.text

    r = client.get("/echo", headers=headers)
    assert r.status_code == 429
    assert r.headers.get("Retry-After") is not None


def test_rate_limit_by_user_bucket():
    fake = _FakeRedis()
    client = _app_with_limit(3, fake)

    # Build a JWT for user bucket
    os.environ["JWT_SECRET"] = "secret123"
    from app_config import app_settings  # ensure settings loaded from env above
    token = create_access_token(
        user_id="user-42",
        username="john",
        roles=["user"],
        secret=app_settings.JWT_SECRET,
        expires_minutes=5,
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Forwarded-For": "5.6.7.8",  # distinct IP per test to avoid collisions
    }

    for _ in range(3):
        r = client.get("/echo", headers=headers)
        assert r.status_code == 200

    r = client.get("/echo", headers=headers)
    assert r.status_code == 429
