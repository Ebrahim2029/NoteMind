import re
from typing import List, Optional, Type
from core.exceptions.note_exceptions import InvalidNoteAttributeException
from core.exceptions.user_exceptions import InvalidUserAttributeException
from email_validator import validate_email, EmailNotValidError

def validate_string(
    value: str,
    field_name: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    exception_cls: Type[Exception] = InvalidNoteAttributeException  # النوع الافتراضي
) -> None:
    """
    Validate string fields with consistent exception types.
    
    Args:
        value: The string value to validate
        field_name: Name of the field for error messages
        min_length: Minimum allowed length (optional)
        max_length: Maximum allowed length (optional)
        exception_cls: نوع الاستثناء المراد رفعه عند الخطأ (افتراضياً InvalidNoteAttributeException)
        
    Raises:
        exception_cls: For all validation errors
    """
    if not isinstance(value, str):
        raise exception_cls(f"{field_name} must be a string")
    
    if not value.strip():
        raise exception_cls(f"{field_name} cannot be empty")
    
    if min_length is not None and len(value) < min_length:
        raise exception_cls(
            f"{field_name} must be at least {min_length} characters"
        )
    
    if max_length is not None and len(value) > max_length:
        raise exception_cls(
            f"{field_name} cannot exceed {max_length} characters"
        )


def validate_tags(tags: List[str]) -> None:
    """
    Validate tags list
    
    Args:
        tags: List of tags to validate
        
    Raises:
        InvalidNoteAttributeException: For invalid tags
    """
    if not isinstance(tags, list):
        raise InvalidNoteAttributeException("Tags must be a list")
    
    for tag in tags:
        validate_string(tag, "Tag", max_length=50)


def validate_color(color: str) -> None:
    """
    Validate hex color format
    
    Args:
        color: Color string to validate
        
    Raises:
        InvalidNoteAttributeException: For invalid color format
    """
    if not isinstance(color, str):
        raise InvalidNoteAttributeException("Color must be a string")
    
    if not color.startswith('#'):
        raise InvalidNoteAttributeException("Color must start with #")
    
    hex_part = color[1:]
    valid_lengths = {3, 6}  # Support both #RGB and #RRGGBB formats
    
    if len(hex_part) not in valid_lengths:
        raise InvalidNoteAttributeException(
            "Color must be in #RGB or #RRGGBB format"
        )
    
    if not all(c.lower() in '0123456789abcdef' for c in hex_part):
        raise InvalidNoteAttributeException(
            "Color contains invalid hex characters"
        )



def validate_email_user(email: str) -> None:
    try:
        # Disable deliverability check
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as e:
       
        raise InvalidUserAttributeException(str(e))