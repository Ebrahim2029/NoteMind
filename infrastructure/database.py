# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app_config import app_settings
import os

# Determine the actual DB name.
# If we're running tests (APP_ENV=testing or under pytest), suffix the DB with "_test".
_db_name = app_settings.POSTGRES_DB
if app_settings.APP_ENV in ("testing", "test") or os.getenv("PYTEST_CURRENT_TEST"):
    _db_name = f"{_db_name}_test"

# Build the SQLAlchemy connection URL for PostgreSQL.
# Tip: If you later need SSL or special params, you can append them here.
DATABASE_URL = (
    f"postgresql://{app_settings.POSTGRES_USER}:{app_settings.POSTGRES_PASSWORD}"
    f"@{app_settings.POSTGRES_HOST}:{app_settings.POSTGRES_PORT}/{_db_name}"
)

# Create a shared Engine.
# - echo=False: silence SQL logs (enable for debugging).
# - pool_size/max_overflow: connection pool sizing.
# - pool_pre_ping=True: validates connections before using (avoids stale connections).
# - pool_recycle=1800s: refresh connections periodically to prevent server timeouts.
# - future=True: use SQLAlchemy 2.x style behavior where applicable.
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=1800,
    future=True,
)

# Factory for DB sessions bound to the engine.
# - expire_on_commit=False keeps objects usable after commit without reloading.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
    future=True,
)

# Base class for declarative models (used in models to define tables).
Base = declarative_base()

def get_db():
    """
    Yield a new SQLAlchemy session and ensure it closes after use.
    Typical usage in FastAPI:
        def endpoint(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
