from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
from sqlalchemy import text


# =========================================
# NotebookModel (represents the "notebooks" table)
# =========================================
class NotebookModel(BaseModel):
    """
    Database model for notebooks.

    Inherits from BaseModel to include:
    - created_at (timestamp of creation)
    - updated_at (timestamp of last update)

    📌 Stores:
    - Notebook metadata (name, color, owner user)
    - Relationships with UserModel (owner) and NoteModel (contained notes)
    """

    __tablename__ = 'notebooks'  # Database table name

    # ==============================
    # Core Fields
    # ==============================

    # Primary key: Unique notebook identifier (UUID)
    # - Automatically generated in PostgreSQL
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))

    # Foreign key: Reference to the owner user
    # - Each notebook belongs to one user
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Notebook name
    # - Required, max length = 100 characters
    name = Column(String(100), nullable=False)

    # Display color for the notebook
    # - Default = light blue (#E3F2FD)
    color = Column(String(20), default='#E3F2FD', nullable=False)

    # ==============================
    # Relationships
    # ==============================

    # Relationship: Notebook belongs to a User
    user = relationship(
        "UserModel",
        back_populates="notebooks",  # Matches "notebooks" field in UserModel
        lazy="joined"                # Eager-load the user when querying a notebook
    )

    # Relationship: Notebook contains multiple Notes
    notes = relationship(
        "NoteModel",
        back_populates="notebook",       # Matches "notebook" field in NoteModel
        cascade="all, delete-orphan",    # If a notebook is deleted, its notes are also deleted
        passive_deletes=True,            # Support DB-level cascades
        lazy="dynamic"                   # Returns a Query object instead of loading all notes at once
    )

    # ==============================
    # Indexes (Performance Optimization)
    # ==============================
    __table_args__ = (
        # Composite B-Tree index:
        # - Optimizes queries filtering by user_id and ordering by created_at
        Index("idx_notebooks_user_created", "user_id", "created_at", postgresql_using="btree"),
    )

    # Alembic migration note (for concurrent index creation in production):
    # op.create_index(
    #     "idx_notebooks_user_created",
    #     "notebooks",
    #     ["user_id", "created_at"],
    #     postgresql_using="btree",
    #     postgresql_concurrently=True
    # )
