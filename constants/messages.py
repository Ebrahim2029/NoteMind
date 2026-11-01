from enum import Enum

"""
General Rule
    - Success = the requested operation was completed as expected.
    - Failed = the operation was not completed as expected 
                (stopped, rolled back, rejected, or inconsistent).
"""
class Status(str, Enum):
    SUCCESS = "Success"
    FAILED = "Failed"

from enum import Enum

# ---------------- Generic ----------------
class InfoMessages(str, Enum):
    ACTION_SUCCESS = "Action completed successfully"   # 200
    NO_CONTENT = "No content available"                # 204


class ErrorMessages(str, Enum):
    BAD_REQUEST = "Invalid input data"                        # 400
    UNAUTHORIZED = "Authentication required"                  # 401
    FORBIDDEN = "You do not have permission"                  # 403
    NOT_FOUND = "Resource not found"                          # 404
    CONFLICT = "Resource conflict"                            # 409
    RATE_LIMIT = "Rate limit exceeded"                        # 429
    SERVER_ERROR = "Internal server error"                    # 500
    SERVICE_UNAVAILABLE = "Service temporarily unavailable"   # 503


# ---------------- Users ----------------
class UserMessages(str, Enum):
    USER_REGISTERED = "User registered successfully"   # 201
    USER_REGISTER_FAILED = "User registration failed"  # 409
    USER_RETRIEVED = "User retrieved successfully"     # 200
    USER_NOT_FOUND = "User not found"                  # 404
    USER_UPDATED = "User updated successfully"         # 200
    USER_UPDATE_FAILED = "Failed to update user"       # 500
    USER_DELETED = "User deleted successfully"         # 204
    USER_DELETE_FAILED = "Failed to delete user"       # 500


# ---------------- Auth ----------------
class AuthMessages(str, Enum):
    LOGIN_SUCCESS = "Login successful"                 # 200
    LOGIN_FAILED = "Invalid username or password"      # 401
    TOKEN_EXPIRED = "Token has expired"                # 401
    TOKEN_INVALID = "Invalid authentication token"     # 401


# ---------------- Notes ----------------
class NoteMessages(str, Enum):
    NOTE_CREATED = "Note created successfully"         # 201
    NOTE_CREATE_FAILED = "Failed to create note"       # 500
    NOTE_RETRIEVED = "Note retrieved successfully"     # 200
    NOTE_NOT_FOUND = "Note not found"                  # 404
    NOTE_UPDATED = "Note updated successfully"         # 200
    NOTE_UPDATE_FAILED = "Failed to update note"       # 500
    NOTE_DELETED = "Note deleted successfully"         # 204
    NOTE_DELETE_FAILED = "Failed to delete note"       # 500
    NOTE_ALREADY_DELETED = "Note is already deleted"   # 409
    NO_NOTES_FOUND = "No notes found"                  # 200


# ---------------- Notebooks ----------------
class NotebookMessages(str, Enum):
    NOTEBOOK_CREATED = "Notebook created successfully"           # 201
    NOTEBOOK_CREATE_FAILED = "Failed to create notebook"         # 500
    NOTEBOOK_UPDATED = "Notebook updated successfully"           # 200
    NOTEBOOK_UPDATE_FAILED = "Failed to update notebook"         # 500
    NOTEBOOK_DELETED = "Notebook deleted successfully"           # 204
    NOTEBOOK_DELETE_FAILED = "Failed to delete notebook"         # 500
    NOTEBOOK_NOT_FOUND = "Notebook not found"                    # 404
    NOTEBOOK_ALREADY_EXISTS = "Notebook already exists"          # 409
    NOTE_ADDED_TO_NOTEBOOK = "Note added to notebook"            # 200
    NOTE_ALREADY_IN_NOTEBOOK = "Note already exists in notebook" # 409
