from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.entities.user import User
from core.repositories.user_repository import UserRepository

# Setup database session
engine = create_engine("postgresql://user:pass@localhost/db")
Session = sessionmaker(bind=engine)
db_session = Session()
user_repo = UserRepository(db_session)

# CREATE - Save a new user
new_user = User(
    username="johndoe",
    email="john@example.com",
    is_active=True,
    preferences={"theme": "dark"}
)
created_user = user_repo.create(new_user)
print(f"Created User: {created_user.username}")

# READ - Get user by ID
user = user_repo.get_by_id(UUID(created_user.id.value))
print(f"Fetched User: {user.email}")

# UPDATE - Modify user
user.username = "john_updated"
updated_user = user_repo.update(user)
print(f"Updated username: {updated_user.username}")

# FILTER - Get user by email
user_by_email = user_repo.get_by_email("john@example.com")
print(f"User by email: {user_by_email.username}")

# DELETE - Deactivate user
user_repo.delete(UUID(created_user.id.value))
print("User deactivated")