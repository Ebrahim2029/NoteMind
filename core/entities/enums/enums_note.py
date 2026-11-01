# core/enums/note_warnings.py
from enum import Enum

class NoteWarnings(Enum):
    # تحقق من العنوان والمحتوى
    TITLE_INVALID = "Title is invalid or too long"
    CONTENT_INVALID = "Content is invalid"
    TAG_INVALID = "Tag is invalid or too long"
    TAGS_INVALID = "Tags list contains invalid values"

    # تحقق من القيم المنطقية
    IS_PINNED_NOT_BOOL = "is_pinned must be a boolean"
    IS_ARCHIVED_NOT_BOOL = "is_archived must be a boolean"
    IS_DELETED_NOT_BOOL = "is_deleted must be a boolean"

    # التذكير
    REMINDER_INVALID = "Reminder must be a datetime object or None"

    # المرفقات
    ATTACHMENT_INVALID = "Attachment path is invalid"


class NoteDefaultsValues(Enum):
    TITLE = "Untitled"
    CONTENT = "No content"
    TAGS = []
    COLOR = "#FFFFFF"
    IS_PINNED = False
    IS_ARCHIVED = False
    IS_DELETED = False
    REMINDER = None
    ATTACHMENT = None