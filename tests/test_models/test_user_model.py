import pytest
from uuid import uuid4
from datetime import datetime
from core.entities.user import User
from core.repositories.models.user_models import UserModel
from app_config import app_settings


def test_user_model_in_test_environment():
    """Test that we're using the correct environment for testing"""
    assert app_settings.APP_ENV == "testing"
    assert app_settings.APP_DEBUG is True

def test_user_model_creation(db_session):
    # Create a new user
    user = UserModel(
        username="testuser",
        email="test@example.com",
        is_active=True,
        preferences={"theme": "dark"}
    )
    
    db_session.add(user)
    db_session.commit()
    
    # Retrieve the user
    retrieved_user = db_session.query(UserModel).filter_by(username="testuser").first()
    
    # Assertions
    assert retrieved_user is not None
    assert retrieved_user.username == "testuser"
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.is_active is True
    assert retrieved_user.preferences == {"theme": "dark"}
    assert isinstance(retrieved_user.id, uuid4().__class__)
    assert isinstance(retrieved_user.created_at, datetime)
    assert isinstance(retrieved_user.updated_at, datetime)

def test_user_model_relationships(db_session):
    # Create a user with notebooks
    user = UserModel(
        username="user_with_notebooks",
        email="notebooks@example.com"
    )
    
    from core.repositories.models.notebook_models import NotebookModel
    notebook = NotebookModel(
        name="Test Notebook",
        color="#FFFFFF",
        user=user
    )
    
    db_session.add(user)
    db_session.add(notebook)
    db_session.commit()
    
    # Test relationship
    assert len(user.notebooks) == 1
    assert user.notebooks[0].name == "Test Notebook"
    assert user.notebooks[0].user_id == user.id