

import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response  # ⬅ add Response
from sqlalchemy.orm import Session

from api.v1.schemas.note_schemas import NoteCreate, NoteUpdate, NoteOut
from api.v1.deps import get_db, requires_role
from core.repositories.note_repository import NoteRepository
from core.entities.note import Note
from utils.outbox import emit_event
from infrastructure.cache import CacheKeys, safe_del_key,redis_client

router = APIRouter(prefix="/api/v1/notes", tags=["notes"])


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(requires_role("user"))])
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteOut:
    
    repo = NoteRepository(db)
    note = Note(
        title=payload.title,
        content=payload.content,
        tags=payload.tags,
        color=payload.color,
        is_pinned=payload.is_pinned,
        is_archived=payload.is_archived,
        reminder=None,
        attachments=payload.attachments,
    )
    if payload.notebook_id:
        try:
            note.notebook_id = uuid.UUID(payload.notebook_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid notebook_id")

    created = repo.create(note)
    return NoteOut(
        id=str(created.id.value),
        notebook_id=str(created.notebook_id) if created.notebook_id else None,
        title=created.title,
        content=created.content,
        tags=created.tags,
        color=created.color,
        is_pinned=created.is_pinned,
        is_archived=created.is_archived,
        is_deleted=created.is_deleted,
        attachments=created.attachments,
    )


@router.get("/{note_id}", response_model=NoteOut,
            dependencies=[Depends(requires_role("user"))])
def get_note(note_id: str, db: Session = Depends(get_db)) -> NoteOut:
    repo = NoteRepository(db)
    try:
        entity = repo.get_by_id(uuid.UUID(note_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Note not found")

    return NoteOut(
        id=str(entity.id.value),
        notebook_id=str(entity.notebook_id) if entity.notebook_id else None,
        title=entity.title,
        content=entity.content,
        tags=entity.tags,
        color=entity.color,
        is_pinned=entity.is_pinned,
        is_archived=entity.is_archived,
        is_deleted=entity.is_deleted,
        attachments=entity.attachments,
    )


@router.put("/{note_id}", response_model=NoteOut,
            dependencies=[Depends(requires_role("user"))])
def update_note(note_id: str, payload: NoteUpdate, db: Session = Depends(get_db)) -> NoteOut:
    repo = NoteRepository(db)
    try:
        existing = repo.get_by_id(uuid.UUID(note_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Note not found")

    existing.title = payload.title
    existing.content = payload.content
    existing.tags = payload.tags
    existing.color = payload.color
    existing.is_pinned = payload.is_pinned
    existing.is_archived = payload.is_archived
    existing.attachments = payload.attachments

    if payload.notebook_id:
        try:
            existing.notebook_id = uuid.UUID(payload.notebook_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid notebook_id")

    updated = repo.update(existing)

    return NoteOut(
        id=str(updated.id.value),
        notebook_id=str(updated.notebook_id) if updated.notebook_id else None,
        title=updated.title,
        content=updated.content,
        tags=updated.tags,
        color=updated.color,
        is_pinned=updated.is_pinned,
        is_archived=updated.is_archived,
        is_deleted=updated.is_deleted,
        attachments=updated.attachments,
    )


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,                              # ⬅ ensure no-body response class
    dependencies=[Depends(requires_role("user"))],
)
def delete_note(note_id: str, db: Session = Depends(get_db)) -> Response:  # ⬅ return Response
    repo = NoteRepository(db)
    try:
        repo.delete(uuid.UUID(note_id))
    except Exception:
        # 404 is fine when the note doesn't exist
        raise HTTPException(status_code=404, detail="Note not found")

    safe_del_key(CacheKeys.NOTE_BY_ID.format(note_id=note_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)  # ⬅ no content
