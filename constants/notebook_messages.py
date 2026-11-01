from enum import Enum
from .messages import Status


class NotebookInfo(str, Enum):
    # ---------------- Notebooks ----------------
    NOTEBOOK_STATUS_SUCCESS = Status.SUCCESS
 
    NOTEBOOK_CREATED = "Notebook created successfully"
    NOTEBOOK_UPDATED = "Notebook updated successfully"
    NOTEBOOK_DELETED = "Notebook deleted successfully"
    NOTEBOOK_NOT_FOUND = "Notebook not found"

    # ---------------- Note Management ----------------
    NOTEBOOK_NOTE_NOT_FOUND = "Note not found in notebook"
    NOTEBOOK_NOTE_ALREADY_EXISTS = "Note already exists in notebook"
    NOTEBOOK_TOO_MANY_NOTES = "Too many notes in notebook"



class NotebookErrors(str, Enum):
    # ---------------- Status ----------------
    NOTEBOOK_STATUS_FAILED = Status.FAILED

    # ---------------- Connection / Transaction ----------------
    NOTEBOOK_DB_CONNECTION_FAILED = "Postgres connection failed"
    NOTEBOOK_DB_TRANSACTION_FAILED = "Database transaction failed"
    NOTEBOOK_DB_COMMIT_FAILED = "Failed to commit notebook transaction"
    NOTEBOOK_DB_ROLLBACK_FAILED = "Failed to rollback notebook transaction"

    # ---------------- CRUD ----------------
    
    NOTEBOOK_CREATE_FAILED = "Failed to create notebook"
    NOTEBOOK_UPDATE_FAILED = "Failed to update notebook"
    NOTEBOOK_DELETE_FAILED = "Failed to delete notebook"
    NOTEBOOK_QUERY_FAILED = "Failed to query notebook"

    # ---------------- Validation ----------------
    NOTEBOOK_INVALID_NAME = "Invalid notebook name"
    NOTEBOOK_INVALID_COLOR = "Invalid notebook color"
    NOTEBOOK_INVALID_NOTE_ID = "Invalid note ID"
    NOTEBOOK_ALREADY_EXISTS = "Notebook already exists"



    # ---------------- Cache / Outbox ----------------
    NOTEBOOK_CACHE_INVALIDATION_FAILED = "Failed to invalidate cache for notebook"
    NOTEBOOK_CACHE_SERIALIZATION_ERROR = "Failed to serialize notebook for cache"
    NOTEBOOK_CACHE_DESERIALIZATION_ERROR = "Failed to deserialize notebook from cache"
    NOTEBOOK_OUTBOX_EMIT_FAILED = "Failed to emit notebook event to outbox"
    NOTEBOOK_OUTBOX_PAYLOAD_INVALID = "Invalid notebook payload for outbox"

    # ---------------- General ----------------
    NOTEBOOK_PERMISSION_DENIED = "Permission denied for this notebook"
    NOTEBOOK_UNKNOWN_ERROR = "Unknown internal notebook error"
