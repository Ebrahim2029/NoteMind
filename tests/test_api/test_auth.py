from __future__ import annotations

import os
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from utils.security import create_access_token
from api.v1.deps import requires_role

# Build a tiny app to validate the dependency behavior
app = FastAPI()

@app.get("/secure-user", dependencies=[Depends(requires_role("user"))])
def secure_user():
    return {"ok": True}

client = TestClient(app)


def _token(roles):
    os.environ["JWT_SECRET"] = "secret123"
    from app_config import app_settings  # ensure loaded
    return create_access_token(
        user_id="u1",
        username="john",
        roles=roles,
        secret=app_settings.JWT_SECRET,
        alg="HS256",
        expires_minutes=5,
    )


def test_requires_role_user_allowed():
    token = _token(["user"])
    r = client.get("/secure-user", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200 and r.json() == {"ok": True}


def test_requires_role_user_forbidden():
    token = _token(["guest"])
    r = client.get("/secure-user", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
