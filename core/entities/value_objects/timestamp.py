from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class Timestamp:
    value: datetime

    def __init__(self, value: Optional[datetime] = None):
        """
        Creates a Timestamp with current time if no value provided.
        """
        object.__setattr__(self, 'value', value or datetime.now())

    def __str__(self) -> str:
        return self.value.isoformat()