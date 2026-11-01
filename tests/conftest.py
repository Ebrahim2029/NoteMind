# /tests/conftest.py
import pytest
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from infrastructure.database import Base
from core.entities.user import User
from core.entities.note import Note
from core.entities.notebook import Notebook
from app_config import app_settings
import os
import sys
from redis import Redis
from infrastructure.cache import redis_client
from infrastructure.database import engine, Base
import uuid
from core.repositories.models.user_models import UserModel
from core.repositories.models.notebook_models import NotebookModel
from core.repositories.models.note_models import NoteModel


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# -------------------------------
# Database Fixtures (PostgreSQL)
# -------------------------------

@pytest.fixture(scope="session")
def db_engine():
    """Create test database and engine with all tables"""
    # Create test database if not exists
    try:
        conn = psycopg2.connect(
            host=app_settings.POSTGRES_HOST,
            port=app_settings.POSTGRES_PORT,
            user=app_settings.POSTGRES_USER,
            password=app_settings.POSTGRES_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE {app_settings.POSTGRES_DB}_test;")
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Database already exists or another error occurred: {e}")

    # Create engine for test database
    db_url = (
        f"postgresql://{app_settings.POSTGRES_USER}:{app_settings.POSTGRES_PASSWORD}@"
        f"{app_settings.POSTGRES_HOST}:{app_settings.POSTGRES_PORT}/"
        f"{app_settings.POSTGRES_DB}_test"
    )
    engine = create_engine(db_url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a fresh database session for each test with transaction rollback"""
    connection = db_engine.connect()
    transaction = connection.begin()
    
    Session = scoped_session(sessionmaker(bind=connection))
    session = Session()
    
    yield session
    
    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()

# -------------------------------
# Redis Fixtures
# -------------------------------

@pytest.fixture(scope="function")
def redis_cleanup():
    """Ensure clean Redis state before each test and cleanup after"""
    redis_client.flushdb()  # Clean before test
    yield
    redis_client.flushdb()  # Clean after test

# -------------------------------
# Sample Data Fixtures
# -------------------------------

@pytest.fixture
def sample_user():
    return {
        "id": uuid.uuid4(),
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
        "preferences": {"theme": "dark"}
    }

@pytest.fixture
def sample_user_entity(sample_user):
    """Return a User entity with sample data"""
    return User(**sample_user)

@pytest.fixture
def sample_notebook(sample_user):
    return {
        "id": uuid.uuid4(),
        "user_id": sample_user["id"],
        "name": "Test Notebook",
        "color": "#FFFFFF"
    }

@pytest.fixture
def sample_notebook_entity(sample_notebook):
    """Return a Notebook entity with sample data"""
    return Notebook(**sample_notebook)

@pytest.fixture
def sample_note(sample_notebook):
    return {
        "id": uuid.uuid4(),
        "notebook_id": sample_notebook["id"],
        "title": "Test Note",
        "content": "This is a test note",
        "tags": ["test", "important"],
        "is_pinned": False
    }

@pytest.fixture
def sample_note_entity(sample_note):
    """Return a Note entity with sample data"""
    return Note(**sample_note)

# -------------------------------
# Model Instance Fixtures
# -------------------------------

@pytest.fixture
def db_user(db_session, sample_user):
    """Create and return a User model instance in database"""
    from core.repositories.models.user_models import UserModel
    user = UserModel(**sample_user)
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def db_notebook(db_session, db_user, sample_notebook):
    """Create and return a Notebook model instance in database"""
    from core.repositories.models.notebook_models import NotebookModel
    notebook = NotebookModel(
        id=sample_notebook["id"],
        user_id=db_user.id,
        name=sample_notebook["name"],
        color=sample_notebook["color"]
    )
    db_session.add(notebook)
    db_session.commit()
    return notebook

@pytest.fixture
def db_note(db_session, db_notebook, sample_note):
    """Create and return a Note model instance in database"""
    from core.repositories.models.note_models import NoteModel
    note = NoteModel(
        id=sample_note["id"],
        notebook_id=db_notebook.id,
        title=sample_note["title"],
        content=sample_note["content"],
        tags=sample_note["tags"],
        is_pinned=sample_note["is_pinned"]
    )
    db_session.add(note)
    db_session.commit()
    return note


@pytest.fixture(scope="session", autouse=True)
def ensure_test_db_and_schema():
    """
    When APP_ENV=testing, make sure the test database exists and that
    the schema (incl. pgcrypto) is created for the engine used by SessionLocal.
    """
    if str(app_settings.APP_ENV).lower() not in ("testing", "test"):
        # On dev/prod we assume DB already exists
        yield
        return

    # 1) Ensure the *database* exists
    try:
        conn = psycopg2.connect(
            host=app_settings.POSTGRES_HOST,
            port=app_settings.POSTGRES_PORT,
            user=app_settings.POSTGRES_USER,
            password=app_settings.POSTGRES_PASSWORD,
            dbname="postgres",  # connect to default to run CREATE DATABASE
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f'CREATE DATABASE "{app_settings.POSTGRES_DB}_test";')
        cur.close()
        conn.close()
    except Exception:
        # already exists or no permission — OK if we can connect later
        pass

    # 2) Create extension + tables on the *same engine* that SessionLocal uses
    with engine.begin() as conn:
        conn.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    Base.metadata.create_all(bind=engine)

    yield

    # Optional: drop all after the whole session
    Base.metadata.drop_all(bind=engine)