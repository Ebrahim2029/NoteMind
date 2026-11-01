"""
CacheMixin: read-through caching + write invalidation.

Integrates directly with infrastructure/cache.py:
- Uses redis_client (thread-safe singleton)
- DEFAULT_TTL_SECONDS as global default
- JSON serialization by default
"""


import json
from typing import Any, Callable, Optional

from infrastructure.cache import redis_client, DEFAULT_TTL_SECONDS  # infrastructure/cache.py alias is 'cache.py'


class CacheMixin:
    """Reusable mixin for repositories needing cache-first reads."""

    def _get_cache_ttl(self) -> int:
        """Default TTL for cached entries (can be overridden)."""
        return DEFAULT_TTL_SECONDS

    def _serialize(self, obj: Any) -> str:
        return json.dumps(obj, default=str)

    def _deserialize(self, data: str) -> Any:
        return json.loads(data)

    def get_cached(self, key: str, loader: Callable[[], Any]) -> Optional[Any]:
        """
        Fetch value from cache or load from DB if missing.
        - key: Redis key
        - loader: function to load from DB (only called on cache miss)
        """
        try:
            hit = redis_client.get(key)
        except Exception:
            # Redis outage: skip cache
            return loader()

        if hit is not None:
            try:
                redis_client.expire(key, self._get_cache_ttl())
            except Exception:
                pass
            return self._deserialize(hit)

        # Miss → DB load
        obj = loader()
        if obj is not None:
            try:
                redis_client.setex(key, self._get_cache_ttl(), self._serialize(obj))
            except Exception:
                pass  # fail-open
        return obj

    def invalidate_keys(self, *keys: str) -> None:
        """Delete cache keys safely."""
        if not keys:
            return
        try:
            redis_client.delete(*keys)
        except Exception:
            pass
