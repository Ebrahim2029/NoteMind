from enum import Enum
from .messages import Status




class UserInfo(str, Enum):
    # ---------------- Users ----------------
    USER_STATUS_SUCCESS = Status.SUCCESS
    
    USER_CREATED = "User created successfully"
    USER_UPDATED = "User updated successfully"
    USER_DELETED = "User deleted successfully"
    USER_NOT_FOUND = "User not found"

    # ---------------- State ----------------
    USER_ALREADY_ACTIVE = "User is already active"
    USER_ALREADY_INACTIVE = "User is already deactivated"


class UserErrors(str, Enum):
    # ---------------- Status ----------------
    USER_STATUS_FAILED = Status.FAILED

    # ---------------- Connection / Transaction ----------------
    USER_DB_CONNECTION_FAILED = "Postgres connection failed"
    USER_DB_TRANSACTION_FAILED = "Database transaction failed"
    USER_DB_COMMIT_FAILED = "Failed to commit user transaction"
    USER_DB_ROLLBACK_FAILED = "Failed to rollback user transaction"

    # ---------------- CRUD ----------------
    USER_CREATE_FAILED = "Failed to create user"
    USER_UPDATE_FAILED = "Failed to update user"
    USER_DELETE_FAILED = "Failed to delete user"
    USER_QUERY_FAILED = "Failed to query user"

    # ---------------- Validation ----------------
    USER_INVALID_USERNAME = "Invalid username"
    USER_INVALID_EMAIL = "Invalid email format"
    USER_INVALID_PREFERENCES = "Invalid preferences format"
    USER_ALREADY_EXISTS = "User already exists"



    # ---------------- Cache / Outbox ----------------
    USER_CACHE_INVALIDATION_FAILED = "Failed to invalidate cache for user"
    USER_CACHE_SERIALIZATION_ERROR = "Failed to serialize user for cache"
    USER_CACHE_DESERIALIZATION_ERROR = "Failed to deserialize user from cache"
    USER_OUTBOX_EMIT_FAILED = "Failed to emit user event to outbox"
    USER_OUTBOX_PAYLOAD_INVALID = "Invalid user payload for outbox"

    # ---------------- General ----------------
    USER_PERMISSION_DENIED = "Permission denied for this user"
    USER_UNKNOWN_ERROR = "Unknown internal user error"
