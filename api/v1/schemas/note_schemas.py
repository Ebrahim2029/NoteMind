

from typing import List, Optional
from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    notebook_id: Optional[str] = None
    title: str = Field(default="Untitled Note", max_length=200)
    content: str = ""
    tags: List[str] = []
    color: str = "#FFFFFF"
    is_pinned: bool = False
    is_archived: bool = False
    reminder: Optional[str] = None
    attachments: List[str] = []


class NoteUpdate(NoteCreate):
    pass


class NoteOut(BaseModel):
    id: str
    notebook_id: Optional[str] = None
    title: str
    content: str
    tags: List[str] = []
    color: str
    is_pinned: bool
    is_archived: bool
    is_deleted: bool
    attachments: List[str] = []
