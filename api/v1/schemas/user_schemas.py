

from typing import Optional, Dict
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(..., max_length=64)
    email: EmailStr
    is_active: bool = True
    preferences: Dict[str, str] = {}


class UserUpdate(BaseModel):
    username: str = Field(..., max_length=64)
    email: EmailStr
    is_active: bool = True
    preferences: Dict[str, str] = {}


class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    is_active: bool
    preferences: Dict[str, str] = {}
