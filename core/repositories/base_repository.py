"""
BaseRepository: shared helpers for repository classes.

Responsibilities:
- DB session handling (no creation here; injected).
- Transactional boundaries for writes (commit/rollback).
- Hooks for after-commit observers (override _after_commit()).
"""



from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


class BaseRepository:
    def __init__(self, db_session: Session):
        self.db: Session = db_session

    @contextmanager
    def _transaction(self) -> Generator[None, None, None]:
        try:
            yield
            self.db.commit()
            self._after_commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise

    # Observer hook
    def _after_commit(self) -> None:  # pragma: no cover (overridden where needed)
        pass


# Database transaction pattern reference:
# https://docs.sqlalchemy.org/en/20/orm/session_transaction.html
#
# Context manager documentation:
# https://docs.python.org/3/library/contextlib.html
#
# Error handling best practices:
# https://docs.sqlalchemy.org/en/20/core/exceptions.html
