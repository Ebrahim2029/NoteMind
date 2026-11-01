

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from api.v1.schemas.user_schemas import UserCreate, UserUpdate, UserOut
from api.v1.deps import get_db, requires_role
from core.repositories.user_repository import UserRepository
from core.entities.user import User
from core.repositories.models.user_models import UserModel  # ORM for list endpoint

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires_role("user"))],
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    repo = UserRepository(db)
    entity = User(
        username=payload.username,
        email=str(payload.email),
        is_active=payload.is_active,
        preferences=payload.preferences,
    )
    created = repo.create(entity)
    return UserOut(
        id=str(created.id.value),
        username=created.username,
        email=created.email,
        is_active=created.is_active,
        preferences=created.preferences,
    )


@router.get(
    "/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(requires_role("user"))],
)
def get_user(user_id: str, db: Session = Depends(get_db)) -> UserOut:
    repo = UserRepository(db)
    try:
        entity = repo.get_by_id(uuid.UUID(user_id))
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")
    if not entity:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(
        id=str(entity.id.value),
        username=entity.username,
        email=entity.email,
        is_active=entity.is_active,
        preferences=entity.preferences,
    )


@router.get(
    "",
    response_model=List[UserOut],
    dependencies=[Depends(requires_role("user"))],
)
def list_users(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> List[UserOut]:
    """
    Lightweight list endpoint. Uses ORM directly for paging to avoid
    loading everything. Mapping to DTO remains explicit.
    """
    rows = (
        db.query(UserModel)
        .order_by(UserModel.created_at.desc() if hasattr(UserModel, "created_at") else UserModel.id)
        .limit(limit)
        .offset(offset)
        .all()
    )
    out: List[UserOut] = []
    for r in rows:
        out.append(
            UserOut(
                id=str(r.id),
                username=r.username,
                email=r.email,
                is_active=getattr(r, "is_active", True),
                preferences=getattr(r, "preferences", {}) or {},
            )
        )
    return out


@router.put(
    "/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(requires_role("user"))],
)
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db)) -> UserOut:
    repo = UserRepository(db)
    try:
        existing = repo.get_by_id(uuid.UUID(user_id))
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    existing.username = payload.username
    existing.email = str(payload.email)
    existing.is_active = payload.is_active
    existing.preferences = payload.preferences

    updated = repo.update(existing)
    return UserOut(
        id=str(updated.id.value),
        username=updated.username,
        email=updated.email,
        is_active=updated.is_active,
        preferences=updated.preferences,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(requires_role("user"))],
)
def delete_user(user_id: str, db: Session = Depends(get_db)) -> Response:
    repo = UserRepository(db)
    try:
        repo.delete(uuid.UUID(user_id))
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
