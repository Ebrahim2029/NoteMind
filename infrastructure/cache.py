# infrastructure/cache.py


from functools import wraps
import json
from typing import Any, Optional
import redis, pickle, inspect, base64
import time
from app_config import app_settings
from redis.exceptions import RedisError
import logging

# Module-level logger for cache operations
logger = logging.getLogger(__name__)

# =========================
# Redis client (thread-safe)
# =========================
# decode_responses=True -> we read/write strings instead of bytes.
# socket_* timeouts keep calls from hanging; adjust as needed.
redis_client = redis.Redis(
    host=app_settings.REDIS_HOST,
    port=app_settings.REDIS_PORT,
    db=app_settings.REDIS_DB,
    decode_responses=True,
    socket_timeout=0.5,
    socket_connect_timeout=0.5,
)

# =========================
# Defaults / Key patterns
# =========================
# Default TTL for cached items (30 minutes).
DEFAULT_TTL_SECONDS = 1800

class CacheKeys:
    """Central place for cache key formats to avoid typos across the codebase."""
    USER_BY_ID = "user:{user_id}"
    USER_BY_EMAIL = "user:email:{email}"
    NOTEBOOK_BY_ID = "notebook:{notebook_id}"
    NOTE_BY_ID = "note:{note_id}"

def _build_cache_key(key_pattern: str, func, args, kwargs):
    """
    Build a cache key by formatting key_pattern with the function's parameters.
    - Ignores 'self' if present (methods).
    - Falls back to a safe concatenation if format placeholders are missing.
    """
    sig = inspect.signature(func)
    bound = sig.bind_partial(*args, **kwargs)
    bound.apply_defaults()
    params = {k: v for k, v in bound.arguments.items() if k != 'self'}
    try:
        return key_pattern.format(**params)
    except KeyError:
        # Fallback to prevent crashes when some placeholders are missing
        return f"{key_pattern}|args={tuple(params.items())}"

# =========================
# Low-level helpers (used by repositories)
# =========================
def set_hash(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """
    Store a JSON-encoded value as a simple Redis STRING with TTL.
    Note: This is *not* a Redis HASH, just a string payload.
    """
    payload = json.dumps(value, default=str)
    redis_client.setex(key, ttl or DEFAULT_TTL_SECONDS, payload)

def safe_set_hash(key: str, mapping: dict, ttl: int | None = None) -> None:
    """
    Store a dict as a Redis HASH (field -> JSON-encoded string).
    - Deletes the key first to avoid WRONGTYPE errors if key existed with another type.
    - Sets TTL on the key.
    - Swallows Redis errors so application flow isn't broken by cache outages.
    """
    ttl = ttl or DEFAULT_TTL_SECONDS
    pipe = redis_client.pipeline()
    pipe.delete(key)  # ensure the key type is correct
    if mapping:
        payload = {k: json.dumps(v, default=str) for k, v in mapping.items()}
        pipe.hset(key, mapping=payload)
    pipe.expire(key, ttl)
    pipe.execute()

def get_hash(key: str) -> dict | None:
    """
    Read a Redis HASH into a Python dict.
    - Returns None if the key doesn't exist.
    - Values are JSON-decoded when possible.
    """
    data = redis_client.hgetall(key)
    if not data:
        return None

    out: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(k, bytes):
            k = k.decode()
        if isinstance(v, bytes):
            v = v.decode()
        try:
            out[k] = json.loads(v)  # decode JSON if possible
        except Exception:
            out[k] = v              # fall back to raw string
    return out

def del_key(key: str) -> None:
    """Delete a Redis key (any type)."""
    redis_client.delete(key)

def refresh_ttl(key: str, ttl: Optional[int] = None) -> None:
    """Refresh the TTL for an existing key."""
    redis_client.expire(key, ttl or DEFAULT_TTL_SECONDS)

# =========================
# Backward-compatible decorator API
# =========================
def cache(key_pattern: str, ttl: int = DEFAULT_TTL_SECONDS):
    """
    Function/method result cache decorator using a Redis STRING.
    - The result is pickled, base64-encoded, and stored under the derived key.
    - On hit, returns the unpickled object.
    - On error, fails open (i.e., just runs the function).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _build_cache_key(key_pattern, func, args, kwargs)
            # Try read
            try:
                raw = redis_client.get(cache_key)  # string because decode_responses=True
                if raw is not None:
                    try:
                        blob = base64.b64decode(raw.encode("utf-8"))
                        return pickle.loads(blob)
                    except Exception:
                        # If the payload is corrupted, delete it and fall through.
                        redis_client.delete(cache_key)
            except RedisError:
                # Redis issue → treat as cache miss and continue
                pass

            # Miss → call function
            result = func(*args, **kwargs)

            # Try write
            try:
                blob = pickle.dumps(result)
                redis_client.setex(cache_key, ttl, base64.b64encode(blob).decode("utf-8"))
            except Exception:
                # Never fail the app because the cache couldn't be written
                pass
            return result
        return wrapper
    return decorator

def invalidate(key_pattern: str):
    """
    Delete one or more keys that match a pattern.
    NOTE: Redis 'KEYS' is O(N); use carefully in production. Prefer specific keys.
    """
    keys = redis_client.keys(key_pattern)
    if keys:
        redis_client.delete(*keys)

# Safer wrappers that never raise (good for tests and resilience)
def safe_del_key(key: str) -> None:
    """Delete a key but swallow Redis errors (non-fatal)."""
    try:
        del_key(key)
    except (RedisError, Exception):
        pass

def safe_refresh_ttl(key: str, ttl: Optional[int] = None) -> None:
    """Refresh TTL but swallow Redis errors (non-fatal)."""
    try:
        refresh_ttl(key, ttl=ttl)
    except (RedisError, Exception):
        pass
