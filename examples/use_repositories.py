# Example usage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.repositories.user_repository import UserRepository
from core.entities.user import User
from app_config import app_settings

db_user = app_settings.POSTGRES_USER
db_password = app_settings.POSTGRES_PASSWORD
db_host = app_settings.POSTGRES_HOST
db_name = app_settings.POSTGRES_DB

engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}")
Session = sessionmaker(bind=engine)
db_session = Session()

user_repo = UserRepository(db_session)

# Create user
new_user = User(username="ali", email="ali@example.com")
created_user = user_repo.create(new_user)

# Get user
user = user_repo.get_by_id(created_user.id.value)

# Update user
user.username = "new_username"
updated_user = user_repo.update(user)

# Delete user
user_repo.delete(updated_user.id.value)