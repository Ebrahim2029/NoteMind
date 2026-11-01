import pytest
from core.entities.notebook import Notebook
from core.entities.note import Note
from core.entities.value_objects.note_id import NoteId
from core.exceptions.notebook_exceptions import NoteNotInNotebookException
from core.exceptions.note_exceptions import InvalidNoteAttributeException

class TestNotebookEntity:
    """Tests for Notebook entity"""

    @pytest.fixture
    def notebook(self):
        return Notebook(name="Test Notebook")

    def test_initialization(self, notebook):
        assert notebook.name == "Test Notebook"
        assert len(notebook.notes) == 0

    def test_invalid_name(self):
        with pytest.raises(InvalidNoteAttributeException):  # Now matches validator
            Notebook(name="A"*101)

    def test_rename_notebook(self, notebook):
        new_name = "New Name"
        notebook.rename(new_name)
        assert notebook.name == new_name

    

    def test_change_color(self, notebook):
        new_color = "#FF0000"
        notebook.change_color(new_color)
        assert notebook.color == new_color

    def test_note_management(self, notebook):
        note_id = NoteId()
        
        notebook.add_note(note_id)
        assert note_id in notebook.notes
        assert notebook.count_notes() == 1
        
        notebook.remove_note(note_id)
        assert note_id not in notebook.notes

    def test_remove_nonexistent_note(self, notebook):
        with pytest.raises(NoteNotInNotebookException):
            notebook.remove_note(NoteId())

    def test_clear_notes(self, notebook):
        notebook.add_note(NoteId())
        notebook.add_note(NoteId())
        notebook.clear_notes()
        assert notebook.is_empty()