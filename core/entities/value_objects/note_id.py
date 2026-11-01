from dataclasses import dataclass
import uuid
from typing import Optional

@dataclass(frozen=True)
class NoteId:
    value: str

    def __init__(self, value: Optional[str] = None):
        """
        Creates a NoteId with a UUID value.
        If value is provided, validates it's a valid UUID.
        """
        object.__setattr__(self, 'value', value or str(uuid.uuid4()))
        
        if not self._is_valid_uuid(self.value):
            raise ValueError("Invalid UUID format for NoteId")

    @staticmethod
    def _is_valid_uuid(uuid_str: str) -> bool:
        try:
            uuid.UUID(uuid_str)
            return True
        except ValueError:
            return False

    def __str__(self) -> str:
        return self.value