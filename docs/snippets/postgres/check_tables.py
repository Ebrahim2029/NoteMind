from core.repositories.models.chat_models import ChatSession, ChatInteraction
from core.repositories.models.base import Base
from infrastructure.database import engine

Base.metadata.create_all(bind=engine)
