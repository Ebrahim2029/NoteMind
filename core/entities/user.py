# /core/entities/user.py
from dataclasses import dataclass, field
from typing import Dict, Optional
from core.entities.value_objects.user_id import UserId
from core.entities.value_objects.timestamp import Timestamp
from core.exceptions.user_exceptions import InvalidUserAttributeException
from utils.validators import validate_string, validate_email_user


@dataclass
class User:
    """
    Represents an application user.

    ✦ Design principles:
    - Single Responsibility: Only manages user-related data and validation.
    - Depends on abstract value objects (`UserId`, `Timestamp`) for identity and time.
    - All changes are performed via dedicated methods to enforce validation rules.
    """

    # ---------------- Core Attributes ----------------
    id: UserId = field(default_factory=UserId)                  # Unique identifier for the user (Value Object)
    username: str = ""                                          # Username (must be 3–30 chars)
    email: str = ""                                             # User email address
    created_date: Timestamp = field(default_factory=Timestamp)  # Creation timestamp
    modified_date: Timestamp = field(default_factory=Timestamp) # Last modification timestamp
    preferences: Dict[str, str] = field(default_factory=dict)   # Arbitrary user preferences (key/value pairs)
    is_active: bool = True                                      # Account status flag (True = active, False = deactivated)

    # ---------------- Initialization & Validation ----------------
    def __post_init__(self):
        """
        Runs immediately after dataclass initialization.
        Ensures all fields are valid.
        """
        self._validate()

    def _validate(self):
        """
        Validate all user attributes:
        - Username must be a string between 3 and 30 characters.
        - Email must follow valid format.
        - `is_active` must be a boolean.
        - `preferences` must be a dictionary.
        """
        validate_string(self.username, "Username", min_length=3, max_length=30)
        validate_email_user(self.email)

        if not isinstance(self.is_active, bool):
            raise InvalidUserAttributeException("is_active must be a boolean")

        if not isinstance(self.preferences, dict):
            raise InvalidUserAttributeException("preferences must be a dictionary")

    # ---------------- User Data Modification ----------------
    def update_username(self, new_username: str):
        """
        Update the username.
        - Validates the new username.
        - Updates `modified_date`.
        """
        validate_string(new_username, "Username", min_length=3, max_length=30)
        self.username = new_username
        self.modified_date = Timestamp()

    def update_email(self, new_email: str):
        """
        Update the user email.
        - Validates the new email format.
        - Updates `modified_date`.
        """
        validate_email_user(new_email)
        self.email = new_email
        self.modified_date = Timestamp()

    # ---------------- User Preferences Management ----------------
    def set_preference(self, key: str, value: str):
        """
        Add or update a user preference (stored as key/value).
        - Both key and value must be valid strings.
        - Updates `modified_date`.
        """
        validate_string(key, "Preference key")
        validate_string(value, "Preference value")
        self.preferences[key] = value
        self.modified_date = Timestamp()

    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a user preference by key.
        - Returns the stored value if it exists.
        - Otherwise returns the provided default (None if not given).
        """
        return self.preferences.get(key, default)

    # ---------------- Account State Management ----------------
    def activate(self):
        """
        Activate the user account.
        Sets `is_active` to True and updates `modified_date`.
        """
        self.is_active = True
        self.modified_date = Timestamp()

    def deactivate(self):
        """
        Deactivate the user account.
        Sets `is_active` to False and updates `modified_date`.
        """
        self.is_active = False
        self.modified_date = Timestamp()
