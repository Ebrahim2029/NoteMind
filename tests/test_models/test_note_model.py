import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from core.repositories.models.note_models import NoteModel
from core.repositories.models.notebook_models import NotebookModel
from core.repositories.models.user_models import UserModel

def test_note_model_creation(db_session):
    # Create user and notebook first
    user = UserModel(username="note_creator", email="creator@example.com")
    notebook = NotebookModel(name="Notes Notebook", user=user)
    
    # Create a note
    note = NoteModel(
        title="Test Note",
        content="This is a test note content.",
        tags=["test", "important"],
        color="#FFFFFF",
        is_pinned=True,
        notebook=notebook
    )
    
    db_session.add_all([user, notebook, note])
    db_session.commit()
    
    # Retrieve the note
    retrieved_note = db_session.query(NoteModel).filter_by(title="Test Note").first()
    
    # Assertions
    assert retrieved_note is not None
    assert retrieved_note.title == "Test Note"
    assert retrieved_note.content == "This is a test note content."
    assert retrieved_note.tags == ["test", "important"]
    assert retrieved_note.color == "#FFFFFF"
    assert retrieved_note.is_pinned is True
    assert retrieved_note.is_archived is False
    assert retrieved_note.is_deleted is False
    assert retrieved_note.notebook_id == notebook.id
    assert isinstance(retrieved_note.id, uuid4().__class__)
    assert isinstance(retrieved_note.created_at, datetime)
    assert isinstance(retrieved_note.updated_at, datetime)

def test_note_model_states(db_session):
    # Create a standalone note (no notebook)
    note = NoteModel(
        title="Standalone Note",
        content="Content",
        is_archived=True,
        is_deleted=True
    )
    
    db_session.add(note)
    db_session.commit()
    
    # Test states
    retrieved_note = db_session.query(NoteModel).filter_by(title="Standalone Note").first()
    assert retrieved_note.is_archived is True
    assert retrieved_note.is_deleted is True
    assert retrieved_note.notebook_id is None

def test_note_model_with_reminder(db_session):
    # Create note with reminder
    reminder_time = datetime.now() + timedelta(days=1)
    note = NoteModel(
        title="Reminder Note",
        content="Don't forget!",
        reminder=reminder_time
    )
    
    db_session.add(note)
    db_session.commit()
    
    # Test reminder
    retrieved_note = db_session.query(NoteModel).filter_by(title="Reminder Note").first()
    assert retrieved_note.reminder == reminder_time

def test_note_model_attachments(db_session):
    # Create note with attachments
    note = NoteModel(
        title="Note with Attachments",
        content="See attachments",
        attachments=["/path/to/file1.pdf", "/path/to/image.jpg"]
    )
    
    db_session.add(note)
    db_session.commit()
    
    # Test attachments
    retrieved_note = db_session.query(NoteModel).filter_by(title="Note with Attachments").first()
    assert len(retrieved_note.attachments) == 2
    assert "/path/to/file1.pdf" in retrieved_note.attachments