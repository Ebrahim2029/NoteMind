from typing import Union, Any, Optional
from pydantic import BaseModel
from .note_schemas import NoteOut
from .user_schemas import UserOut
from .notebook_schemas import NotebookOut
from .auth_schemas import TokenResponse


class StandardResponse(BaseModel):
    status: str  # "success", "warning", "error"
    message: str
    detail: Optional[Any] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Note created successfully",
                "data": {"id": "123", "title": "My Note"}
            }
        }



class NoteResponse(StandardResponse):
    detail: Union[NoteOut, None]

class UserResponse(StandardResponse):
    detail: Union[UserOut, None]

class NotebookResponse(StandardResponse):
    detail: Union[NotebookOut, None]

class TokenStandardResponse(StandardResponse):
    detail: Union[TokenResponse, None]
