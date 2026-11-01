# tests/test_cache.py
import time
import uuid
import pytest

from infrastructure.cache import (
    redis_client,
    safe_set_hash,
    get_hash,
    safe_del_key,
    safe_refresh_ttl,
    invalidate,
    cache as cache_decorator,
    _build_cache_key,
    DEFAULT_TTL_SECONDS,
)


@pytest.fixture(scope="module", autouse=True)
def ensure_redis():
    """Skip these tests cleanly if Redis isn't reachable."""
    try:
        redis_client.ping()
    except Exception:
        pytest.skip("Redis is not available for cache tests")


def test_safe_set_hash_and_get_hash_roundtrip_types():
    key = f"test:hash:roundtrip:{uuid.uuid4()}"
    mapping = {"title": "Hello", "count": 3, "flag": True, "tags": ["x", "y"]}
    safe_set_hash(key, mapping, ttl=10)
    loaded = get_hash(key)
    assert loaded == mapping
    # cleanup
    safe_del_key(key)


def test_safe_set_hash_overwrites_wrongtype_without_wrongtype_error():
    key = f"test:hash:wrongtype:{uuid.uuid4()}"
    # First, store a plain string at the same key (different Redis type).
    redis_client.set(key, "plain-str", ex=10)
    # Now store a hash; implementation deletes the key first to avoid WRONGTYPE.
    safe_set_hash(key, {"x": 1}, ttl=10)
    assert get_hash(key) == {"x": 1}
    safe_del_key(key)


def test_safe_refresh_ttl_extends_expiry():
    key = f"test:hash:ttl:{uuid.uuid4()}"
    safe_set_hash(key, {"a": 1}, ttl=1)   # expires quickly
    time.sleep(0.6)
    # Extend the TTL before it expires
    safe_refresh_ttl(key, ttl=2)
    time.sleep(1.1)
    # Should still exist because we extended TTL
    assert get_hash(key) == {"a": 1}
    # Wait for it to expire now
    time.sleep(1.2)
    assert get_hash(key) is None
    safe_del_key(key)  # no-op if already gone


def test_safe_del_key_and_invalidate_pattern():
    prefix = f"test:invalidate:{uuid.uuid4()}"
    k1 = f"{prefix}:k1"
    k2 = f"{prefix}:k2"
    safe_set_hash(k1, {"a": 1}, ttl=30)
    safe_set_hash(k2, {"b": 2}, ttl=30)
    # Pattern delete both
    invalidate(f"{prefix}:*")
    assert get_hash(k1) is None
    assert get_hash(k2) is None
    # Also verify single-key delete is harmless on missing key
    safe_del_key(k1)


def test_cache_decorator_caches_and_expires():
    calls = {"n": 0}

    @cache_decorator("test:decor:{x}", ttl=1)
    def compute(x: int) -> int:
        calls["n"] += 1
        return x * x

    # First call computes and caches
    assert compute(5) == 25
    assert calls["n"] == 1

    # Second call hits cache (no extra call)
    assert compute(5) == 25
    assert calls["n"] == 1

    # After TTL, recomputes
    time.sleep(1.1)
    assert compute(5) == 25
    assert calls["n"] == 2

    # Cleanup cached keys
    invalidate("test:decor:*")


def test__build_cache_key_ignores_self_and_formats_params():
    # Dummy method-like function: first arg would be 'self'
    def dummy(self, x, y=2):  # noqa: ANN001
        return (x, y)

    key = _build_cache_key("k:{x}:{y}", dummy, args=(object(), 10), kwargs={})
    assert key == "k:10:2"
