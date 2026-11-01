

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from api.v1.schemas.notebook_schemas import NotebookCreate, NotebookUpdate, NotebookOut
from api.v1.deps import get_db, requires_role
from core.repositories.notebook_repository import NotebookRepository
from core.entities.notebook import Notebook
from core.repositories.models.notebook_models import NotebookModel  # ORM for list endpoint

router = APIRouter(prefix="/api/v1/notebooks", tags=["notebooks"])


@router.post(
    "",
    response_model=NotebookOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires_role("user"))],
)
def create_notebook(payload: NotebookCreate, db: Session = Depends(get_db)) -> NotebookOut:
    repo = NotebookRepository(db)
    try:
        owner = uuid.UUID(payload.user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")
    entity = Notebook(
        user_id=owner,
        name=payload.name,
        color=payload.color,
    )
    created = repo.create(entity)
    return NotebookOut(
        id=str(created.id.value),
        user_id=str(created.user_id),
        name=created.name,
        color=created.color,
    )


@router.get(
    "/{notebook_id}",
    response_model=NotebookOut,
    dependencies=[Depends(requires_role("user"))],
)
def get_notebook(notebook_id: str, db: Session = Depends(get_db)) -> NotebookOut:
    repo = NotebookRepository(db)
    try:
        entity = repo.get_by_id(uuid.UUID(notebook_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if not entity:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return NotebookOut(
        id=str(entity.id.value),
        user_id=str(entity.user_id),
        name=entity.name,
        color=entity.color,
    )


@router.get(
    "",
    response_model=List[NotebookOut],
    dependencies=[Depends(requires_role("user"))],
)
def list_notebooks(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: str | None = Query(None),
) -> List[NotebookOut]:
    """
    List notebooks with optional filter by user_id.
    """
    q = db.query(NotebookModel)
    if user_id:
        try:
            q = q.filter(NotebookModel.user_id == uuid.UUID(user_id))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid user_id")
    rows = (
        q.order_by(NotebookModel.name.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [
        NotebookOut(
            id=str(r.id),
            user_id=str(r.user_id),
            name=r.name,
            color=r.color,
        )
        for r in rows
    ]


@router.put(
    "/{notebook_id}",
    response_model=NotebookOut,
    dependencies=[Depends(requires_role("user"))],
)
def update_notebook(notebook_id: str, payload: NotebookUpdate, db: Session = Depends(get_db)) -> NotebookOut:
    repo = NotebookRepository(db)
    try:
        existing = repo.get_by_id(uuid.UUID(notebook_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if not existing:
        raise HTTPException(status_code=404, detail="Notebook not found")

    existing.name = payload.name
    existing.color = payload.color
    updated = repo.update(existing)
    return NotebookOut(
        id=str(updated.id.value),
        user_id=str(updated.user_id),
        name=updated.name,
        color=updated.color,
    )


@router.delete(
    "/{notebook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(requires_role("user"))],
)
def delete_notebook(notebook_id: str, db: Session = Depends(get_db)) -> Response:
    repo = NotebookRepository(db)
    try:
        repo.delete(uuid.UUID(notebook_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
