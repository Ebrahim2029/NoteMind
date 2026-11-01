"""
Cache key helpers for Redis.

Key patterns (must stay stable across the project):
- note:<note_id>
- search:<user_id>:<qhash>
- chunk:<note_id>:<version>:<idx>
- session:<session_id>

This module centralizes key building to avoid drift.
"""



import hashlib
from typing import Iterable, List, Tuple
from uuid import UUID

DEFAULT_TTL_SECONDS = 900  # 15 minutes — project default


def note_key(note_id: UUID | str) -> str:
    return f"note:{note_id}"


def search_key(user_id: UUID | str, query: str) -> str:
    qhash = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
    return f"search:{user_id}:{qhash}"


def chunk_key(note_id: UUID | str, version: int, idx: int) -> str:
    return f"chunk:{note_id}:{version}:{idx}"


def session_key(session_id: str) -> str:
    return f"session:{session_id}"


def invalidation_for_create_note(user_id: UUID | str) -> List[str]:
    # New content can change any search results for that user
    return [f"search:{user_id}:*"]


def invalidation_for_update_note(note_id: UUID | str, user_id: UUID | str) -> List[str]:
    return [note_key(note_id), f"chunk:{note_id}:*", f"search:{user_id}:*"]


def invalidation_for_delete_note(note_id: UUID | str, user_id: UUID | str) -> List[str]:
    return [note_key(note_id), f"chunk:{note_id}:*", f"search:{user_id}:*"]


def flatten_patterns(patterns: Iterable[str]) -> Tuple[str, ...]:
    """Helper for tests."""
    return tuple(patterns)
