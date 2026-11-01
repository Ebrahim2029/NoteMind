

import uuid
from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.ai.clients.chroma_client import ChromaClient
from api.v1.schemas.auth_schemas import RegisterRequest, LoginRequest, TokenResponse
from api.v1.schemas.response_schemas import TokenStandardResponse
from api.v1.deps import get_db
from core.repositories.user_repository import UserRepository
from core.entities.user import User
from utils.security import create_access_token
from app_config import app_settings

from api.v1.schemas.response_schemas import TokenStandardResponse
from constants.auth_messages import AuthInfo, AuthErrors

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

logger = logging.getLogger(__name__)

@router.post("/register", response_model=TokenStandardResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)) -> TokenStandardResponse:
    """DEV-friendly register: creates a User and immediately returns a JWT.

    NOTE: No password storage yet. For production, add a credential store and hashing.
    """
    users = UserRepository(db)

    # Check if email exists
    existing = users.get_by_email(str(req.email))
    if existing:
        raise HTTPException(status_code=409, detail=AuthErrors.REGISTER_FAILED)
    # Create user
    entity = User(username=req.username, email=str(req.email), is_active=True, preferences={})
    created = users.create(entity)
    # Create JWT token
    token = create_access_token(
        user_id=str(created.id.value),
        username=created.username,
        roles=["user"],
        secret=app_settings.JWT_SECRET,
        alg=getattr(app_settings, "JWT_ALG", "HS256"),
        expires_minutes=int(getattr(app_settings, "JWT_EXP_MINUTES", 60)),
    )
    return TokenStandardResponse(
        status=AuthInfo.AUTH_STATUS_SUCCESS,
        message=AuthInfo.REGISTER_SUCCESS,  # or just "User registered successfully"
        detail=TokenResponse(access_token=token)
    )


@router.post("/login", response_model=TokenResponse)
def login(
    req: LoginRequest, 
    db: Session = Depends(get_db)
    ) -> TokenResponse:
    """DEV-friendly login: looks up user by email or username, then returns a JWT.

    NOTE: No password verification yet. For production, validate a hashed password.
    """
    users = UserRepository(db)

    user = None
    if req.email:
        user = users.get_by_email(str(req.email))
    elif req.username:
        # No direct "get_by_username" helper; list by email only in repo.
        # For dev, try a simple scan via ORM if available, else 404.
        from core.repositories.models.user_models import UserModel  # ORM model
        user = db.query(UserModel).filter(UserModel.username == req.username).first()
        if user:
            # Convert ORM → domain quickly for token issuance
            from core.entities.user import UserId, Timestamp
            user = User(
                id=UserId(value=str(user.id)),
                username=user.username,
                email=user.email,
                is_active=getattr(user, "is_active", True),
                preferences=getattr(user, "preferences", {}) or {},
                created_date=Timestamp(value=getattr(user, "created_at", None)),
                modified_date=Timestamp(value=getattr(user, "updated_at", None)),
            )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # ✅ Ensure Chroma Tenant exists for this user
    chroma = ChromaClient()
    try:
        chroma.tenants.get(str(user.id.value))
        logger.info(f"[ChromaClient] Tenant exists for user {user.id.value}")
    except Exception:
        chroma.tenants.create(str(user.id.value))
        logger.info(f"[ChromaClient] Created tenant for user {user.id.value}")
        
    token = create_access_token(
        user_id=str(user.id.value),
        username=user.username,
        roles=["user"],
        secret=app_settings.JWT_SECRET,
        alg=getattr(app_settings, "JWT_ALG", "HS256"),
        expires_minutes=int(getattr(app_settings, "JWT_EXP_MINUTES", 60)),
    )
    return TokenResponse(access_token=token)
