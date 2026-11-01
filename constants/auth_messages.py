from enum import Enum
from .messages import Status


class AuthInfo(str, Enum):
    # ---------------- Auth Status Success ----------------
    AUTH_STATUS_SUCCESS = Status.SUCCESS

    # ---------------- Auth Messages Success ----------------
    LOGIN_SUCCESS = "Login successful"
    LOGOUT_SUCCESS = "Logout successful"
    REGISTER_SUCCESS = "User registered successfully"
   
    # ---------------- System / General ----------------
    ACTION_SUCCESS = "Action completed successfully"
   



class AuthErrors(str, Enum):
    # ---------------- Auth Status Failed ----------------
    AUTH_STATUS_FAILED = Status.FAILED

    # ---------------- Auth Messages Failed ----------------
    LOGIN_FAILED = "Invalid username or password"
    LOGOUT_FAILED = "Logout failed"
    REGISTER_FAILED = "User registration failed"
    TOKEN_EXPIRED = "Token has expired"
    TOKEN_INVALID = "Invalid authentication token"

    # ---------------- System / General ----------------
    ACTION_FAILED = "Action failed"
    PERMISSION_DENIED = "You do not have permission to perform this action"
    SERVER_ERROR = "An unexpected error occurred. Please try again later"