# /tests/test_repositories/test_notebook_repository.py
import pytest
import uuid
from core.repositories.notebook_repository import NotebookRepository
from core.entities.notebook import Notebook
from core.exceptions.notebook_exceptions import NotebookNotFoundException
from infrastructure.cache import CacheKeys
from tests.conftest import db_session

class TestNotebookRepository:
    def test_notebook_creation_with_notes(self, db_session, sample_notebook, sample_note):
        from core.repositories.models.user_models import UserModel
        from core.repositories.models.notebook_models import NotebookModel
        from core.repositories.models.note_models import NoteModel

        # أنشئ مستخدم بالـ user_id المستخدم في الدفتر
        user = UserModel(
            id=sample_notebook["user_id"],
            username="test_user",
            email="test_user@example.com",
            is_active=True,
            preferences={"theme": "dark"},
        )
        db_session.add(user)

        notebook_model = NotebookModel(**sample_notebook)
        note_model = NoteModel(**sample_note)

        db_session.add(notebook_model)
        db_session.add(note_model)
        db_session.commit()
        
        repo = NotebookRepository(db_session)
        notebook = repo.get_by_id(sample_notebook["id"])
        
        assert notebook.id == sample_notebook["id"]
        assert len(notebook.notes) == 1
        assert notebook.notes[0].title == sample_note["title"]

    def test_get_by_user_caching(self, db_session, redis_cleanup, sample_user, sample_notebook):
        from core.repositories.models.user_models import UserModel
        from core.repositories.models.notebook_models import NotebookModel
        
        # Setup test data
        user_model = UserModel(**sample_user)
        notebook_model = NotebookModel(**sample_notebook)
        db_session.add(user_model)
        db_session.add(notebook_model)
        db_session.commit()
        
        repo = NotebookRepository(db_session)
        
        # First call - should cache
        result1 = repo.get_by_user(sample_user["id"])
        assert len(result1["notebooks"]) == 1
        
        # Verify cache
        cache_key = CacheKeys.USER_NOTEBOOKS.format(user_id=sample_user["id"])
        assert redis_client.exists(cache_key)
        
        # Second call - should hit cache
        db_session.expire_all()  # Clear session to ensure cache is used
        result2 = repo.get_by_user(sample_user["id"])
        assert result2 == result1

    def test_batch_update(self, db_session, sample_notebook):
        from core.repositories.models.notebook_models import NotebookModel
        
        # Setup test data
        notebook1 = NotebookModel(**sample_notebook)
        notebook2 = NotebookModel(
            id=uuid.uuid4(),
            user_id=sample_notebook["user_id"],
            name="Notebook 2",
            color="#000000"
        )
        db_session.add_all([notebook1, notebook2])
        db_session.commit()
        
        repo = NotebookRepository(db_session)
        
        # Prepare updates
        notebooks_to_update = [
            Notebook(id=notebook1.id, user_id=notebook1.user_id, name="Updated 1", color=notebook1.color),
            Notebook(id=notebook2.id, user_id=notebook2.user_id, name="Updated 2", color="#FF0000")
        ]
        
        updated = repo.update_batch(notebooks_to_update)
        
        assert len(updated) == 2
        assert {n.name for n in updated} == {"Updated 1", "Updated 2"}