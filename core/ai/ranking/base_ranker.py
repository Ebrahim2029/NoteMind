

from datetime import datetime, timezone


class BaseRanker:
    def rank(self, *args, **kwargs):
        raise NotImplementedError


def _normalize_time_score(ts: datetime | None, now: datetime) -> float:
    """Map recency to [0,1] with a simple half-life model (30 days)."""
    if ts is None:
        return 0.5
    delta = (now - ts).total_seconds()
    half_life = 30 * 86400
    score = 0.5 ** (delta / half_life)
    return max(0.0, min(1.0, score))
