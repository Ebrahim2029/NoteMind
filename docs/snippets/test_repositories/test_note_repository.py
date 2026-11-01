# /tests/test_repositories/test_note_repository.py
import pytest
import uuid
from datetime import datetime, timedelta
from core.repositories.note_repository import NoteRepository
from core.entities.note import Note
from core.exceptions.note_exceptions import NoteNotFoundException
from infrastructure.cache import CacheKeys

class TestNoteRepository:
    def test_advanced_search(self, db_session, sample_note):
        from core.repositories.models.note_models import NoteModel
        
        # Setup test data
        note1 = NoteModel(**sample_note)
        note2 = NoteModel(
            id=uuid.uuid4(),
            notebook_id=sample_note["notebook_id"],
            title="Another Note",
            content="Contains important information",
            tags=["important"]
        )
        db_session.add_all([note1, note2])
        db_session.commit()
        
        repo = NoteRepository(db_session)
        
        # Test tag search
        results = repo.advanced_search({
            "tags": ["important"]
        })
        assert len(results["notes"]) == 1
        assert results["notes"][0].title == "Another Note"
        
        # Test text search
        results = repo.advanced_search({
            "query": "important"
        })
        assert len(results["notes"]) == 1
        
        # Test combined search
        results = repo.advanced_search({
            "notebook_id": sample_note["notebook_id"],
            "query": "test"
        })
        assert len(results["notes"]) == 1
        assert results["notes"][0].title == "Test Note"

    def test_recently_accessed(self, db_session, redis_cleanup, sample_note):
        from core.repositories.models.note_models import NoteModel
        
        # Setup test data
        note1 = NoteModel(**sample_note)
        note2 = NoteModel(
            id=uuid.uuid4(),
            notebook_id=sample_note["notebook_id"],
            title="Recent Note",
            content="This should appear first",
            modified_date=datetime.now()
        )
        db_session.add_all([note1, note2])
        db_session.commit()
        
        repo = NoteRepository(db_session)
        user_id = uuid.uuid4()  # Mock user ID
        
        # First call - should populate Redis
        recent = repo.get_recently_accessed(user_id)
        assert len(recent) == 2
        assert recent[0].title == "Recent Note"
        
        # Verify Redis data
        cache_key = f"user:{user_id}:recent_notes"
        assert redis_client.zcard(cache_key) == 2
        
        # Second call - should use Redis
        db_session.expire_all()  # Clear session
        recent_cached = repo.get_recently_accessed(user_id)
        assert recent_cached == recent