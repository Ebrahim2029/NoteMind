# /core/entities/note.py
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from core.entities.value_objects.note_id import NoteId
from core.entities.value_objects.timestamp import Timestamp
from core.exceptions.note_exceptions import InvalidNoteAttributeException
from utils.validators import validate_string, validate_tags
from .enums.enums_note import NoteWarnings, NoteDefaultsValues


@dataclass
class Note:
    """
    Domain entity representing a Note inside the note-taking application.

    💡 Design follows SOLID principles:
    - SRP (Single Responsibility Principle): Only responsible for holding and validating note data.
    - OCP (Open/Closed Principle): Can be extended without modifying core logic.
    - LSP (Liskov Substitution Principle): Can be subclassed without breaking functionality.
    - ISP (Interface Segregation Principle): Does not enforce unnecessary methods.
    - DIP (Dependency Inversion Principle): Depends on value objects and abstractions.
    """

    # ----------------------------------------------------------------------
    # 📌 Attributes (data fields of the Note entity)
    # ----------------------------------------------------------------------

    id: NoteId = field(default_factory=NoteId)                        # Unique Note identifier (Value Object)
    notebook_id: Optional[int] = None                                 # Reference to the parent Notebook ID
    title: str = NoteDefaultsValues.TITLE.value                       # Note title (default value provided by enum)
    content: str = NoteDefaultsValues.CONTENT.value                   # Main body/content of the note
    created_date: Timestamp = field(default_factory=Timestamp)        # Timestamp when the note was created
    modified_date: Timestamp = field(default_factory=Timestamp)       # Timestamp of the last modification
    tags: List[str] = field(default_factory=list)                     # List of tags/labels for the note
    color: str = NoteDefaultsValues.COLOR.value                       # Color associated with the note
    is_pinned: bool = NoteDefaultsValues.IS_PINNED.value              # Whether the note is pinned to the top
    is_archived: bool = NoteDefaultsValues.IS_ARCHIVED.value          # Whether the note is archived
    is_deleted: bool = NoteDefaultsValues.IS_DELETED.value            # Whether the note is logically deleted
    reminder: Optional[datetime] = NoteDefaultsValues.REMINDER.value  # Optional reminder datetime
    attachments: List[str] = field(default_factory=list)              # List of file attachments

    # ----------------------------------------------------------------------
    # 📌 Initialization & Validation
    # ----------------------------------------------------------------------
    def __post_init__(self):
        """
        Called automatically after dataclass initialization.
        Ensures that all attributes are validated before the object is used.
        """
        self._validate()

    def _validate(self):
        """
        Validate all attributes of the note.
        Ensures strings are within allowed limits and booleans have correct types.
        """
        validate_string(self.title, "Title", max_length=200)
        validate_string(self.content, "Content")
        validate_tags(self.tags)

        if not isinstance(self.is_pinned, bool):
            raise InvalidNoteAttributeException(NoteWarnings.IS_PINNED_NOT_BOOL.value)
        if not isinstance(self.is_archived, bool):
            raise InvalidNoteAttributeException(NoteWarnings.IS_ARCHIVED_NOT_BOOL.value)
        if not isinstance(self.is_deleted, bool):
            raise InvalidNoteAttributeException(NoteWarnings.IS_DELETED_NOT_BOOL.value)

    # ----------------------------------------------------------------------
    # ✏️ Content & Title Management
    # ----------------------------------------------------------------------
    def update_content(self, new_content: str):
        """Update the note content and refresh modified_date timestamp."""
        validate_string(new_content, "Content")
        self.content = new_content
        self.modified_date = Timestamp()
        self._validate()

    def update_title(self, new_title: str):
        """Update the note title and refresh modified_date timestamp."""
        validate_string(new_title, "Title", max_length=200)
        self.title = new_title
        self.modified_date = Timestamp()
        self._validate()

    # ----------------------------------------------------------------------
    # 🏷️ Tags Management
    # ----------------------------------------------------------------------
    def add_tag(self, tag: str):
        """Add a new tag to the note if it does not already exist."""
        validate_string(tag, "Tag", max_length=50)
        if tag not in self.tags:
            self.tags.append(tag)
            self.modified_date = Timestamp()

    def remove_tag(self, tag: str):
        """Remove an existing tag from the note."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.modified_date = Timestamp()

    # ----------------------------------------------------------------------
    # 📌 Pinning & Archiving
    # ----------------------------------------------------------------------
    def toggle_pin(self):
        """Toggle the pinned status of the note."""
        self.is_pinned = not self.is_pinned
        self.modified_date = Timestamp()

    def archive(self):
        """Mark the note as archived."""
        self.is_archived = True
        self.modified_date = Timestamp()

    def unarchive(self):
        """Unmark the note as archived."""
        self.is_archived = False
        self.modified_date = Timestamp()

    # ----------------------------------------------------------------------
    # 🗑️ Soft Delete & Restore
    # ----------------------------------------------------------------------
    def delete(self):
        """Mark the note as logically deleted (soft delete)."""
        self.is_deleted = True
        self.modified_date = Timestamp()

    def restore(self):
        """Restore a previously soft-deleted note."""
        self.is_deleted = False
        self.modified_date = Timestamp()

    # ----------------------------------------------------------------------
    # ⏰ Reminder Management
    # ----------------------------------------------------------------------
    def set_reminder(self, reminder: Optional[datetime]):
        """
        Set a reminder datetime for the note, or clear it by passing None.
        Ensures the provided value is a datetime if not None.
        """
        if reminder is not None and not isinstance(reminder, datetime):
            raise InvalidNoteAttributeException(NoteWarnings.REMINDER_INVALID.value)
        self.reminder = reminder
        self.modified_date = Timestamp()

    # ----------------------------------------------------------------------
    # 📎 Attachments Management
    # ----------------------------------------------------------------------
    def add_attachment(self, attachment_path: str):
        """Add an attachment (file path) to the note if not already present."""
        validate_string(attachment_path, "Attachment path")
        if attachment_path not in self.attachments:
            self.attachments.append(attachment_path)
            self.modified_date = Timestamp()

    def remove_attachment(self, attachment_path: str):
        """Remove an attachment (file path) from the note if it exists."""
        if attachment_path in self.attachments:
            self.attachments.remove(attachment_path)
            self.modified_date = Timestamp()
