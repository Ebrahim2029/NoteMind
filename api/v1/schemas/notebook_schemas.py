

from typing import Optional
from pydantic import BaseModel, Field


class NotebookCreate(BaseModel):
    user_id: str  # owner
    name: str = Field(..., max_length=120)
    color: str = "#FFFFFF"


class NotebookUpdate(BaseModel):
    name: str = Field(..., max_length=120)
    color: str = "#FFFFFF"


class NotebookOut(BaseModel):
    id: str
    user_id: str
    name: str
    color: str
