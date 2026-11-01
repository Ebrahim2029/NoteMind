from __future__ import annotations

from utils.cache_keys import (
    invalidation_for_create_note,
    invalidation_for_update_note,
    invalidation_for_delete_note,
    flatten_patterns,
)


def test_invalidation_patterns():
    u = "user-1"
    n = "note-1"
    assert "search:user-1:*" in flatten_patterns(invalidation_for_create_note(u))
    pats = flatten_patterns(invalidation_for_update_note(n, u))
    assert f"note:{n}" in pats and f"chunk:{n}:*" in pats
    pats = flatten_patterns(invalidation_for_delete_note(n, u))
    assert f"note:{n}" in pats and f"search:{u}:*" in pats
