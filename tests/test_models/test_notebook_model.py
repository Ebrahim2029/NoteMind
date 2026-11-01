import pytest
from uuid import uuid4
from datetime import datetime
from core.repositories.models.notebook_models import NotebookModel
from core.repositories.models.user_models import UserModel

def test_notebook_model_creation(db_session):
    # First create a user
    user = UserModel(
        username="notebook_owner",
        email="owner@example.com"
    )
    db_session.add(user)
    db_session.commit()
    
    # Create a notebook
    notebook = NotebookModel(
        name="My Notebook",
        color="#E3F2FD",
        user_id=user.id
    )
    
    db_session.add(notebook)
    db_session.commit()
    
    # Retrieve the notebook
    retrieved_notebook = db_session.query(NotebookModel).filter_by(name="My Notebook").first()
    
    # Assertions
    assert retrieved_notebook is not None
    assert retrieved_notebook.name == "My Notebook"
    assert retrieved_notebook.color == "#E3F2FD"
    assert retrieved_notebook.user_id == user.id
    assert isinstance(retrieved_notebook.id, uuid4().__class__)
    assert isinstance(retrieved_notebook.created_at, datetime)
    assert isinstance(retrieved_notebook.updated_at, datetime)

def test_notebook_model_relationships(db_session):
    # Create user and notebook
    user = UserModel(username="rel_user", email="rel@example.com")
    notebook = NotebookModel(name="Rel Notebook", user=user)
    
    from core.repositories.models.note_models import NoteModel
    note = NoteModel(
        title="Test Note",
        content="Note content",
        notebook=notebook
    )
    
    db_session.add_all([user, notebook, note])
    db_session.commit()
    
    # Test relationships
    assert notebook.user == user
    assert notebook.notes.count() == 1
    assert notebook.notes.first().title == "Test Note"
    
    # Test cascade delete
    db_session.delete(notebook)
    db_session.commit()
    
    assert db_session.query(NoteModel).filter(NoteModel.notebook_id == notebook.id).count() == 0