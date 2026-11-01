from core.entities.notebook import Notebook
from core.repositories.notebook_repository import NotebookRepository

notebook_repo = NotebookRepository(db_session)

# CREATE - Save new notebook
new_notebook = Notebook(
    user_id=UUID(created_user.id.value),
    name="My First Notebook",
    color="#FF5733"
)
created_notebook = notebook_repo.create(new_notebook)
print(f"Created Notebook: {created_notebook.name}")

# READ - Get notebook by ID
notebook = notebook_repo.get_by_id(UUID(created_notebook.id.value))
print(f"Fetched Notebook: {notebook.color}")

# UPDATE - Modify notebook
notebook.name = "Updated Notebook Name"
updated_notebook = notebook_repo.update(notebook)
print(f"Updated notebook name: {updated_notebook.name}")

# FILTER - Get all notebooks for user
user_notebooks = notebook_repo.get_by_user(UUID(created_user.id.value))
print(f"User has {len(user_notebooks)} notebooks")

# DELETE - Remove notebook
notebook_repo.delete(UUID(created_notebook.id.value))
print("Notebook deleted")