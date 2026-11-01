# /core/entities/notebook.py
from dataclasses import dataclass, field
from typing import List, Optional, Set
from core.entities.value_objects.notebook_id import NotebookId
from core.entities.value_objects.note_id import NoteId
from core.entities.value_objects.timestamp import Timestamp
from core.exceptions.notebook_exceptions import (
    InvalidNotebookAttributeException,
    NoteNotInNotebookException
)
from utils.validators import validate_string
from .enums.enums_notebook import NotebookDefaults, NotebookWarnings


# ==============================
# Notebook domain entity
# ==============================
@dataclass
class Notebook:
    """
    Represents a notebook that groups and organizes notes.

    Design principles:
    - SRP (Single Responsibility): This class is only responsible for notebook data
      and operations on that data (name/color, membership of notes).
    - Immutable-by-default idea for identifiers and timestamps: `id` and `created_date`
      are set on creation. Updates alter `modified_date`.
    - Updates are performed through dedicated methods that validate inputs.
    """

    # ==============================
    # Core Attributes
    # ==============================
    id: NotebookId = field(default_factory=NotebookId)          # Unique notebook identifier (Value Object)
    user_id: Optional[int] = None                               # Owning user identifier (kept as Optional[int] to match your current design)
    name: str = NotebookDefaults.DEFAULT_NAME.value             # Notebook display name (with sane default)
    created_date: Timestamp = field(default_factory=Timestamp)  # Creation timestamp
    modified_date: Timestamp = field(default_factory=Timestamp) # Last modification timestamp
    notes: Set[NoteId] = field(default_factory=set)             # Set of contained note IDs (Set prevents duplicates)
    color: str = NotebookDefaults.DEFAULT_COLOR.value           # UI color for the notebook (light blue by default)

    # ==============================
    # Post-init validation
    # ==============================
    def __post_init__(self):
        """
        Runs immediately after dataclass initialization to validate initial state.
        """
        self._validate()

    def _validate(self):
        """
        Validate core attributes:
        - `name` and `color` must be non-empty strings within length limits.
        - `notes` must be a set (used for uniqueness).
        """
        validate_string(self.name, "Notebook name", max_length=100)
        validate_string(self.color, "Notebook color", max_length=20)

        if not isinstance(self.notes, set):
            raise InvalidNotebookAttributeException(NotebookWarnings.NOTES_MUST_BE_SET.value)

    # ==============================
    # Basic attribute mutators
    # ==============================
    def rename(self, new_name: str):
        """
        Change the notebook name.
        Updates `modified_date` to reflect the change.
        """
        validate_string(new_name, "Notebook name", max_length=100)
        self.name = new_name
        self.modified_date = Timestamp()

    def change_color(self, new_color: str):
        """
        Change the notebook color.
        Updates `modified_date` to reflect the change.
        """
        validate_string(new_color, "Notebook color", max_length=20)
        self.color = new_color
        self.modified_date = Timestamp()

    # ==============================
    # Managing notes inside this notebook
    # ==============================
    def add_note(self, note_id: NoteId):
        """
        Add a note to the notebook.
        - Ensures the provided value is a NoteId.
        - Uses a set to avoid duplicates.
        - Updates `modified_date` after a successful change.
        """
        if not isinstance(note_id, NoteId):
            raise InvalidNotebookAttributeException(NotebookWarnings.INVALID_NOTE_ID.value)
        self.notes.add(note_id)
        self.modified_date = Timestamp()

    def remove_note(self, note_id: NoteId):
        """
        Remove a note from the notebook.
        - Validates the type.
        - Raises NoteNotInNotebookException if the note is not present.
        - Updates `modified_date` after removal.
        """
        if not isinstance(note_id, NoteId):
            raise InvalidNotebookAttributeException(NotebookWarnings.INVALID_NOTE_ID.value)
        if note_id not in self.notes:
            raise NoteNotInNotebookException(f"{note_id} {NotebookWarnings.NOTE_NOT_IN_NOTEBOOK.value}")
        self.notes.remove(note_id)
        self.modified_date = Timestamp()

    def contains_note(self, note_id: NoteId) -> bool:
        """
        Check whether a note is currently in this notebook.
        - Validates the type before checking membership.
        """
        if not isinstance(note_id, NoteId):
            raise InvalidNotebookAttributeException(NotebookWarnings.INVALID_NOTE_ID.value)
        return note_id in self.notes

    def clear_notes(self):
        """
        Remove all notes from the notebook.
        Updates `modified_date` after clearing.
        """
        self.notes.clear()
        self.modified_date = Timestamp()

    # ==============================
    # Inspection helpers
    # ==============================
    def count_notes(self) -> int:
        """
        Return the number of notes currently in the notebook.
        """
        return len(self.notes)

    def is_empty(self) -> bool:
        """
        Return True if the notebook contains no notes.
        """
        return self.count_notes() == 0
