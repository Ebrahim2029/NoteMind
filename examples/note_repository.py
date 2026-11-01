from datetime import datetime, timedelta
from core.entities.note import Note
from core.repositories.note_repository import NoteRepository
import uuid
note_repo = NoteRepository(db_session)

# CREATE - Save new note
new_note = Note(
    notebook_id=UUID(created_notebook.id.value),
    title="Important Ideas",
    content="This is my first note content",
    tags=["ideas", "important"],
    color="#E3F2FD",
    is_pinned=True,
    reminder=datetime.now() + timedelta(days=1)
)
created_note = note_repo.create(new_note)
print(f"Created Note: {created_note.title}")

# READ - Get note by ID
note = note_repo.get_by_id(UUID(created_note.id.value))
print(f"Fetched Note: {note.tags}")

# UPDATE - Modify note
note.content = "Updated note content with more details"
note.tags.append("updated")
updated_note = note_repo.update(note)
print(f"Updated note content: {updated_note.content}")

# FILTER - Get notes by notebook
notes_in_notebook = note_repo.get_by_notebook(UUID(created_notebook.id.value))
print(f"Notebook has {len(notes_in_notebook)} notes")

# FILTER - Search notes
search_results = note_repo.search("details")
print(f"Found {len(search_results)} notes matching 'details'")

# DELETE - Soft delete note
note_repo.delete(UUID(created_note.id.value))
print("Note marked as deleted")

# FILTER - Include deleted notes
all_notes = note_repo.get_by_notebook(
    UUID(created_notebook.id.value),
    include_deleted=True
)
print(f"Including deleted, notebook has {len(all_notes)} notes")