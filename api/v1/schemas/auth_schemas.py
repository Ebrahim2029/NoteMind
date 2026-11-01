

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., max_length=64)
    email: EmailStr


class LoginRequest(BaseModel):
    # For dev/testing we allow either email or username.
    # Password is omitted until a credential store is added.
    email: Optional[EmailStr] = None
    username: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
