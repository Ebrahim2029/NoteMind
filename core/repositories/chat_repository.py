# core/repositories/chat_repository.py
from sqlalchemy.orm import Session
from core.repositories.models.chat_models import ChatSession, ChatInteraction

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, user_id: str) -> ChatSession:
        session = ChatSession(user_id=user_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def add_interaction(self, session_id: str, role: str, content: str, notes=None, extra_metadata=None, quoted_note_id=None):
        interaction = ChatInteraction(
            session_id=session_id,
            role=role,
            content=content,
            notes=notes,
            extra_metadata=extra_metadata,
            quoted_note_id=quoted_note_id, 
        )
        self.db.add(interaction)
        self.db.commit()
        return interaction
