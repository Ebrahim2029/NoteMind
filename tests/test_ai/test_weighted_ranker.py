from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.ai.ranking.weighted_ranker import (
    NoteCandidate,
    WeightedRanker,
    compute_weighted_score,
)


def test_compute_weighted_score_bounds():
    assert 0.0 <= compute_weighted_score(1.2, -1, 2) <= 1.0
    assert compute_weighted_score(0, 0, 0) == 0.0


def test_ranker_orders_by_weighted_score():
    now = datetime.now(timezone.utc)
    c1 = NoteCandidate(id="A", updated_at=now - timedelta(days=1))
    c2 = NoteCandidate(id="B", updated_at=now - timedelta(days=90))
    ranked = WeightedRanker().rank([c1, c2], [0.83, 0.90], now=now)
    assert len(ranked) == 2
    # ensure sorting by score desc
    assert ranked[0][1] >= ranked[1][1]
