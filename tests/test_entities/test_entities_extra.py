import pytest
from datetime import datetime
from core.entities.note import Note
from core.entities.notebook import Notebook
from core.entities.value_objects.note_id import NoteId
from core.entities.value_objects.notebook_id import NotebookId
from core.entities.value_objects.timestamp import Timestamp
from core.exceptions.note_exceptions import InvalidNoteAttributeException
from core.exceptions.notebook_exceptions import InvalidNotebookAttributeException, NoteNotInNotebookException
import pytest
from core.entities.user import User
from core.entities.value_objects.user_id import UserId
from core.exceptions.user_exceptions import InvalidUserAttributeException

# =====================
# Tests for Note
# =====================

def test_note_validate_invalid_types():
    # is_pinned not bool
    with pytest.raises(InvalidNoteAttributeException):
        Note(title="Valid", content="Content", is_pinned="yes")
    # is_archived not bool
    with pytest.raises(InvalidNoteAttributeException):
        Note(title="Valid", content="Content", is_archived="yes")
    # is_deleted not bool
    with pytest.raises(InvalidNoteAttributeException):
        Note(title="Valid", content="Content", is_deleted="yes")

def test_set_reminder_invalid_type():
    note = Note(title="t", content="c")
    with pytest.raises(InvalidNoteAttributeException):
        note.set_reminder("not-a-datetime")

def test_set_reminder_valid_none_and_datetime():
    note = Note(title="t", content="c")
    note.set_reminder(None)
    note.set_reminder(datetime.now())
    assert isinstance(note.reminder, datetime)

# =====================
# Tests for Notebook
# =====================

def test_notebook_validate_invalid_notes_type():
    with pytest.raises(InvalidNotebookAttributeException):
        Notebook(notes="not-a-set")

def test_notebook_add_note_invalid_type():
    nb = Notebook()
    with pytest.raises(InvalidNotebookAttributeException):
        nb.add_note("not-a-NoteId")

def test_notebook_remove_note_invalid_type():
    nb = Notebook()
    with pytest.raises(InvalidNotebookAttributeException):
        nb.remove_note("not-a-NoteId")

def test_notebook_remove_note_not_found():
    nb = Notebook()
    note_id = NoteId()
    with pytest.raises(NoteNotInNotebookException):
        nb.remove_note(note_id)

def test_notebook_contains_note_invalid_type():
    nb = Notebook()
    with pytest.raises(InvalidNotebookAttributeException):
        nb.contains_note("not-a-NoteId")

def test_notebook_contains_note_true_false():
    nb = Notebook()
    note_id = NoteId()
    nb.add_note(note_id)
    assert nb.contains_note(note_id) is True
    nb.remove_note(note_id)
    assert nb.contains_note(note_id) is False

# =====================
# Tests for __str__ methods
# =====================

def test_noteid_str_and_validation():
    valid_id = str(NoteId())
    assert isinstance(str(NoteId(valid_id)), str)
    with pytest.raises(ValueError):
        NoteId("invalid-uuid")

def test_notebookid_str_and_validation():
    valid_id = str(NotebookId())
    assert isinstance(str(NotebookId(valid_id)), str)
    with pytest.raises(ValueError):
        NotebookId("invalid-uuid")

def test_timestamp_str():
    ts = Timestamp(datetime(2025, 8, 10, 12, 30, 45))
    assert "2025-08-10T12:30:45" in str(ts)
