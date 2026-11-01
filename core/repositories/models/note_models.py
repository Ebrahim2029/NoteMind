from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from .base import BaseModel
from sqlalchemy import text


# =========================================
# NoteModel (represents the "notes" table)
# =========================================
class NoteModel(BaseModel):
    """
    Database model for storing notes.

    Inherits from BaseModel to include:
    - created_at
    - updated_at

    📌 Contains:
    - Core note data (title, content, tags, color, etc.)
    - State flags (pinned, archived, deleted)
    - Reminder functionality
    - Attachments
    - Relationship with NotebookModel
    """

    __tablename__ = 'notes'  # Table name in the database

    # ==============================
    # Core Fields
    # ==============================

    # Primary key: Unique note identifier (UUID)
    # - Automatically generated in PostgreSQL using gen_random_uuid()
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))

    # Foreign key: Reference to the notebook this note belongs to
    # - ondelete="CASCADE" means deleting a notebook deletes all its notes
    notebook_id = Column(UUID(as_uuid=True), ForeignKey('notebooks.id', ondelete="CASCADE"), nullable=True)

    # Title of the note
    # - Default = "Untitled Note"
    # - Max length = 200 characters
    title = Column(String(200), default='Untitled Note', nullable=False)

    # Main content of the note
    # - Stored as text
    content = Column(Text, default='', nullable=False)

    # Tags associated with the note
    # - Stored as an array of strings (max length = 50 per tag)
    # - Default = empty list
    tags = Column(ARRAY(String(50)), default=list, nullable=False)

    # Color used for note display
    # - Default = white ("#FFFFFF")
    color = Column(String(20), default='#FFFFFF', nullable=False)

    # ==============================
    # State Flags
    # ==============================

    # Whether the note is pinned to the top
    is_pinned = Column(Boolean, default=False, nullable=False)

    # Whether the note is archived
    is_archived = Column(Boolean, default=False, nullable=False)

    # Whether the note is soft-deleted
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Optional reminder datetime for the note
    reminder = Column(DateTime, nullable=True)

    # ==============================
    # Attachments
    # ==============================

    # Array of file paths or URLs attached to the note
    attachments = Column(ARRAY(String), default=list, nullable=False)


    
    # Last accessed timestamp
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    # ==============================
    # Relationships
    # ==============================

    # Relationship: Each note belongs to exactly one Notebook
    notebook = relationship(
        "NotebookModel", 
        back_populates="notes",   # Matches the "notes" relationship in NotebookModel
        lazy="selectin"           # Eager-load the notebook when querying a note
    )

    # ==============================
    # Indexes (Performance Optimization)
    # ==============================
    __table_args__ = (
        # GIN index on tags array
        # - Optimizes queries like "WHERE tags && ARRAY[...]"
        Index("idx_notes_tags_gin", "tags", postgresql_using="gin"),

        # Composite B-Tree index
        # - Optimizes queries filtering by notebook, deletion status, and created_at
        Index(
            "idx_notes_book_del_created",
            "notebook_id", "is_deleted", "created_at",
            postgresql_using="btree"
        ),
    )

    # Alembic migration note (manual creation with concurrent indexes):
    # op.create_index("idx_notes_tags_gin", "notes", ["tags"], postgresql_using="gin", postgresql_concurrently=True)
    # op.create_index("idx_notes_book_del_created", "notes", ["notebook_id", "is_deleted", "created_at"],
    #                 postgresql_using="btree", postgresql_concurrently=True)
