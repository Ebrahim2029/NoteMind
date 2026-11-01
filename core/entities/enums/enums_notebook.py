from enum import Enum

class NotebookDefaults(Enum):
    DEFAULT_NAME = "New Notebook"
    DEFAULT_COLOR = "#E3F2FD"



class NotebookWarnings(Enum):
    INVALID_NAME = "Notebook name is invalid or too long"
    INVALID_COLOR = "Notebook color is invalid or too long"
    NOTES_MUST_BE_SET = "Notes must be a set"
    INVALID_NOTE_ID = "Must provide a valid NoteId"  
       
    NOTE_NOT_IN_NOTEBOOK = "Note not found in notebook"

