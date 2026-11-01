import pytest
from datetime import datetime, timedelta
from core.entities.note import Note
from core.exceptions.note_exceptions import InvalidNoteAttributeException

class TestNoteEntity:
    """اختبارات كيان الملاحظة"""

    def test_initialization(self):
        note = Note(title="Test", content="Content")
        assert note.title == "Test"
        assert not note.is_pinned
        assert isinstance(note.id, type(Note().id))

    # -------- اختبارات المحتوى والعنوان --------
    def test_update_content(self):
        note = Note()
        new_content = "New content"
        note.update_content(new_content)
        assert note.content == new_content

    def test_update_title(self):
        note = Note()
        new_title = "New Title"
        note.update_title(new_title)
        assert note.title == new_title

    # -------- اختبارات الوسوم --------
    def test_tag_management(self):
        note = Note()
        note.add_tag("important")
        assert "important" in note.tags
        
        note.remove_tag("important")
        assert "important" not in note.tags

    # -------- اختبارات الحالات --------
    def test_status_management(self):
        note = Note()
        
        # التثبيت
        note.toggle_pin()
        assert note.is_pinned
        
        # الأرشفة
        note.archive()
        assert note.is_archived
        note.unarchive()
        assert not note.is_archived
        
        # الحذف
        note.delete()
        assert note.is_deleted
        note.restore()
        assert not note.is_deleted

    # -------- اختبارات التذكيرات --------
    def test_reminder_management(self):
        note = Note()
        reminder = datetime.now() + timedelta(days=1)
        
        note.set_reminder(reminder)
        assert note.reminder == reminder
        
        note.set_reminder(None)
        assert note.reminder is None

    # -------- اختبارات المرفقات --------
    def test_attachments(self):
        note = Note()
        attachment = "/path/to/file.pdf"
        
        note.add_attachment(attachment)
        assert attachment in note.attachments
        
        note.remove_attachment(attachment)
        assert attachment not in note.attachments