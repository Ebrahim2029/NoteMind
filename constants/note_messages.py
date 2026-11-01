"""
from app.constants.note_errors import NoteErrors
import logging

logger = logging.getLogger("my_app.notes")

def get_by_id(self, note_id):
    try:
        return super().get_by_id(note_id)
    except Exception as e:
        logger.error(f"{NoteErrors.NOTE_QUERY_FAILED}: {e}")
        raise Exception(NoteErrors.NOTE_QUERY_FAILED.value)

# in API
@router.get("/notes/{note_id}")
def get_note(note_id: str):
    note = repo.get_by_id(note_id)
    if not note:
        return {
            "status": "error",
            "code": NoteErrors.NOTE_NOT_FOUND.name,
            "message": NoteErrors.NOTE_NOT_FOUND.value
        }
    return {"status": "success", "message": "Note retrieved", "data": note}

"""


from enum import Enum
from .messages import Status



class NoteInfo(str, Enum):
    # ---------------- Notes ----------------
    NOTE_STATUS_SUCCESS = Status.SUCCESS
    NOTE_CREATED = "Note created successfully"
    NOTE_UPDATED = "Note updated successfully"
    NOTE_DELETED = "Note deleted successfully"
    NOTE_RESTORED = "Note restored successfully"
    NOTE_PINNED = "Note pinned"
    NOTE_UNPINNED = "Note unpinned"
    NOTE_ARCHIVED = "Note archived"
    NOTE_UNARCHIVED = "Note unarchived"
    NOTE_NOT_FOUND = "Note not found"

    # ---------------- State / Flags ----------------
    NOTE_ALREADY_DELETED = "Note is already deleted"
    NOTE_ALREADY_ARCHIVED = "Note is already archived"
    NOTE_ALREADY_PINNED = "Note is already pinned"


class NoteErrors(str, Enum):
    # ---------------- Status ----------------
    NOTE_STATUS_FAILED = Status.FAILED

    # ---------------- Connection / Transaction ----------------
    NOTE_DB_CONNECTION_FAILED = "Postgres connection failed"
    NOTE_DB_TRANSACTION_FAILED = "Database transaction failed"
    NOTE_DB_COMMIT_FAILED = "Failed to commit transaction"
    NOTE_DB_ROLLBACK_FAILED = "Failed to rollback transaction"

    # ---------------- CRUD ----------------
    NOTE_CREATE_FAILED = "Failed to create note"
    NOTE_UPDATE_FAILED = "Failed to update note"
    NOTE_DELETE_FAILED = "Failed to delete note"
    NOTE_RESTORE_FAILED = "Failed to restore note"
    NOTE_QUERY_FAILED = "Failed to query notes"

    # ---------------- Validation ----------------
    NOTE_INVALID_TITLE = "Invalid note title"
    NOTE_INVALID_CONTENT = "Invalid note content"
    NOTE_INVALID_TAGS = "Invalid tags format"
    NOTE_INVALID_COLOR = "Invalid note color value"
    NOTE_INVALID_REMINDER = "Invalid reminder datetime"
    NOTE_INVALID_ATTACHMENT = "Invalid attachment format"

    # ---------------- Constraints ----------------
    NOTE_TITLE_TOO_LONG = "Note title exceeds maximum length"
    NOTE_TAG_TOO_LONG = "Tag exceeds maximum length"
    NOTE_TOO_MANY_TAGS = "Too many tags for note"
    NOTE_ATTACHMENT_TOO_LONG = "Attachment path exceeds maximum length"
    NOTE_ATTACHMENT_DUPLICATE = "Duplicate attachment detected"


    # ---------------- Cache / Outbox ----------------
    NOTE_CACHE_INVALIDATION_FAILED = "Failed to invalidate cache for note"
    NOTE_CACHE_SERIALIZATION_ERROR = "Failed to serialize note for cache"
    NOTE_CACHE_DESERIALIZATION_ERROR = "Failed to deserialize note from cache"
    NOTE_OUTBOX_EMIT_FAILED = "Failed to emit note event to outbox"
    NOTE_OUTBOX_PAYLOAD_INVALID = "Invalid note payload for outbox"

    # ---------------- General ----------------
    NOTE_PERMISSION_DENIED = "Permission denied for this note"
    NOTE_UNKNOWN_ERROR = "Unknown internal note error"
