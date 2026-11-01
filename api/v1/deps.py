

from typing import Generator, Optional, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from infrastructure.database import SessionLocal
from utils.security import decode_token, has_role, UserClaims
from app_config import app_settings

# ----- DB dependency -----
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----- Auth dependencies -----
bearer = HTTPBearer(auto_error=True)

def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> UserClaims:
    token = creds.credentials
    try:
        claims = decode_token(
            token,
            secret=app_settings.JWT_SECRET,
            alg=getattr(app_settings, "JWT_ALG", "HS256"),
        )
        return claims
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def requires_role(role: str) -> Callable[[UserClaims], UserClaims]:
    def _dep(claims: UserClaims = Depends(get_current_user)) -> UserClaims:
        if not has_role(claims, role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return claims
    return _dep
