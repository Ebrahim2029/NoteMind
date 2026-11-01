from sqlalchemy import Column, String, Boolean, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
from sqlalchemy.orm import relationship
from sqlalchemy import text


class UserModel(BaseModel):
    """
    Database model for application users.

    Inherits from BaseModel to include:
    - created_at
    - updated_at
    """

    __tablename__ = 'users'  # Table name in PostgreSQL

    # -------------------------
    # Core columns
    # -------------------------

    # Primary key: UUID generated in PostgreSQL using gen_random_uuid()
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))

    # Username:
    # - Unique and non-null
    # - Max length = 30 characters
    username = Column(String(30), unique=True, nullable=False)

    # Email:
    # - Unique and non-null
    # - Max length = 255 characters
    email = Column(String(255), unique=True, nullable=False)

    # Account status flag:
    # - Defaults to True (active)
    is_active = Column(Boolean, default=True, nullable=False)

    # Arbitrary user preferences as JSON:
    # - Non-null; default to empty object
    preferences = Column(JSON, default={}, nullable=False)

    # -------------------------
    # Relationships
    # -------------------------

    # One-to-many: a user owns multiple notebooks
    notebooks = relationship(
        "NotebookModel",              # Target model (user's notebooks)
        back_populates="user",        # Matches `user` relationship in NotebookModel
        cascade="all, delete-orphan", # Deleting a user deletes all their notebooks
        passive_deletes=True,         # Allow DB-level cascades without loading children
        lazy="selectin"               # Efficient eager loading with a second SELECT
    )

    # (Optional) Useful index examples you might add via Alembic:
    __table_args__ = (
     Index("idx_users_email", "email", postgresql_using="btree"),
    )
