"""
JWT + RBAC utilities.

- HS256 JWT with short helpers to encode/decode.
- Pydantic UserClaims for typed payloads.
- Role guard helpers (user/admin).
"""



import time
from typing import Any, Dict, Iterable, Optional

import jwt
from pydantic import BaseModel, Field, ValidationError


class JwtError(Exception):
    """Wrap JWT-related errors to keep dependencies clean."""


class UserClaims(BaseModel):
    sub: str = Field(..., description="User ID")
    username: str
    roles: list[str] = []
    exp: int


def _now() -> int:
    return int(time.time())


def create_access_token(
    *,
    user_id: str,
    username: str,
    roles: Iterable[str] | None,
    secret: str,
    alg: str = "HS256",
    expires_minutes: int = 60,
) -> str:
    """Create a signed JWT."""
    payload: Dict[str, Any] = {
        "sub": user_id,
        "username": username,
        "roles": list(roles or []),
        "exp": _now() + (expires_minutes * 60),
    }
    try:
        return jwt.encode(payload, secret, algorithm=alg)
    except Exception as e:  # pragma: no cover
        raise JwtError(str(e)) from e


def decode_token(token: str, *, secret: str, alg: str = "HS256") -> UserClaims:
    """Decode and validate a token → typed claims."""
    try:
        data = jwt.decode(token, secret, algorithms=[alg])
        return UserClaims(**data)
    except (jwt.PyJWTError, ValidationError) as e:
        raise JwtError(str(e)) from e


def has_role(claims: UserClaims, required: str) -> bool:
    """Case-insensitive role check."""
    want = required.lower()
    return any(r.lower() == want for r in (claims.roles or []))
