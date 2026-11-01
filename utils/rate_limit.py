"""
Rate limiting middleware (IP + User buckets) backed by Redis.

- Fixed-window counter per minute (fast and simple).
- Two buckets are enforced:
  1) IP bucket: rl:ip:<ip>:<window_start_min>
  2) User bucket (if JWT present): rl:user:<user_id>:<window_start_min>

The request is allowed only if **both** buckets are under the limit.
Responds with 429 Too Many Requests on limit breach and sets helpful headers:
- X-RateLimit-Limit
- X-RateLimit-Remaining
- Retry-After (seconds until window resets)

Configuration:
- limit_per_minute (int): default = int(ENV["API_RATE_LIMIT_PER_MIN"] or 120)
- exclude_paths (set[str]): paths to skip (e.g., /health, /docs)
"""



import os
import time
from typing import Iterable, Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from infrastructure.cache import redis_client  # uses your infrastructure/cache.py
from utils.security import decode_token, UserClaims
from app_config import app_settings


def _now_ts() -> int:
    return int(time.time())


def _window_start(now: int) -> int:
    # minute window anchor (epoch minutes)
    return now // 60


def _seconds_until_window_end(now: int) -> int:
    return 60 - (now % 60)


def _client_ip(request: Request) -> str:
    # Trust X-Forwarded-For if present (use first hop)
    xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    # Fallback to ASGI client info
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _user_id_from_auth(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        claims = decode_token(token, secret=app_settings.JWT_SECRET, alg=getattr(app_settings, "JWT_ALG", "HS256"))
        return claims.sub
    except Exception:
        # Invalid tokens are treated as anonymous (IP bucket still applies)
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        limit_per_minute: Optional[int] = None,
        exclude_paths: Optional[Iterable[str]] = None,
    ):
        super().__init__(app)
        self.limit = int(limit_per_minute or os.getenv("API_RATE_LIMIT_PER_MIN", "120"))
        self.exclude = set(exclude_paths or {"/health", "/docs", "/openapi.json", "/redoc"})

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip excluded paths
        if request.url.path in self.exclude:
            return await call_next(request)

        now = _now_ts()
        win = _window_start(now)
        ttl = _seconds_until_window_end(now)

        # Identify
        ip = _client_ip(request)
        uid = _user_id_from_auth(request)

        # Build keys
        ip_key = f"rl:ip:{ip}:{win}"
        user_key = f"rl:user:{uid}:{win}" if uid else None

        # Count in Redis (fail-open if Redis not available)
        over_limit, remaining = False, self.limit
        try:
            ip_count = redis_client.incr(ip_key)
            if ip_count == 1:
                redis_client.expire(ip_key, ttl)
            # Track "max" across buckets
            current = ip_count

            if user_key:
                u_count = redis_client.incr(user_key)
                if u_count == 1:
                    redis_client.expire(user_key, ttl)
                current = max(current, u_count)

            if current > self.limit:
                over_limit = True
            remaining = max(0, self.limit - current)
        except Exception:
            # Redis outage → allow traffic
            over_limit = False
            remaining = self.limit  # conservative header

        # If over limit -> 429
        if over_limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": str(0),
                    "Retry-After": str(ttl),
                },
            )

        # Proceed
        resp = await call_next(request)
        # Attach headers for observability
        resp.headers["X-RateLimit-Limit"] = str(self.limit)
        resp.headers["X-RateLimit-Remaining"] = str(remaining)
        return resp
