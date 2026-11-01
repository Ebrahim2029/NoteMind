# core/repositories/models/chat_models.py
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from core.repositories.models.base import Base
import uuid
from datetime import datetime, timezone


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    notebook_id = Column(String, index=True, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ✅ Relationship: one session → many interactions
    interactions = relationship("ChatInteraction", back_populates="session", cascade="all, delete-orphan")


class ChatInteraction(Base):
    __tablename__ = "chat_interactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)

    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    notes = Column(JSON, nullable=True)  # store retrieved notes snapshot
    extra_metadata = Column(JSON, nullable=True)  # store language, intents, etc.
    quoted_note_id = Column(String, nullable=True, index=True)  # ✅ new, with index

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # ✅ Relationship back to session
    session = relationship("ChatSession", back_populates="interactions")
