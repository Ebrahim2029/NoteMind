# Import necessary SQLAlchemy tools
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, func

# ==============================
# Define the Base for all models
# ==============================
# Base is the root class from which all database models will inherit.
from infrastructure.database import Base


# ==============================
# Shared BaseModel class
# ==============================
class BaseModel(Base):
    """
    Abstract base class that provides common fields for all database models.

    📌 Notes:
    - `__abstract__ = True` means this class itself will NOT create a database table.
      Instead, it is designed to be inherited by other models.
    - Automatically includes `created_at` and `updated_at` timestamps
      to track record lifecycle events.
    """

    __abstract__ = True  # Prevents creating a separate table for this base class

    # ==============================
    # Shared Columns
    # ==============================

    # Record creation timestamp
    # - Automatically set to current time when the row is inserted.
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Record last update timestamp
    # - Automatically set to current time when the row is created.
    # - Automatically updated whenever the row is modified.
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
