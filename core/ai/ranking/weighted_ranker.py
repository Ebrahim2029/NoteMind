

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Sequence, Tuple

from core.ai.ranking.base_ranker import BaseRanker, _normalize_time_score


def compute_weighted_score(
    semantic_similarity: float,
    recency_score: float,
    last_accessed_score: float,
    is_pinned: bool = False,
    is_archived: bool = False,
) -> float:
    """
    Relevance = 0.7 * semantic + 0.2 * recency + 0.1 * last_accessed,
    with boosts for pinned notes and penalties for archived notes.
    All base terms must be in [0,1].
    """
    semantic_similarity = max(0.0, min(1.0, semantic_similarity))
    recency_score = max(0.0, min(1.0, recency_score))
    last_accessed_score = max(0.0, min(1.0, last_accessed_score))

    base_score = (
        0.7 * semantic_similarity
        + 0.2 * recency_score
        + 0.1 * last_accessed_score
    )

    # Apply modifiers
    if is_pinned:
        base_score += 0.05  # small boost for pinned
    if is_archived:
        base_score -= 0.10  # penalty for archived

    return max(0.0, min(1.0, base_score))


@dataclass(frozen=True)
class NoteCandidate:
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_accessed_at: datetime | None = None
    title: str | None = None
    tags: list[str] | None = None
    is_pinned: bool | None = None
    is_archived: bool | None = None
    reminders: str | None = None
    content: str | None = None


class WeightedRanker(BaseRanker):
    def rank(
        self,
        candidates: Sequence[NoteCandidate],
        semantic_scores: Sequence[float],
        now: datetime | None = None,
    ) -> List[Tuple[NoteCandidate, float]]:
        now = now or datetime.now(timezone.utc)
        results: List[Tuple[NoteCandidate, float]] = []
        for note, sem in zip(candidates, semantic_scores):
            rec = _normalize_time_score(note.updated_at or note.created_at, now)
            last = _normalize_time_score(note.last_accessed_at or note.updated_at, now)
            score = compute_weighted_score(sem, rec, last)
            results.append((note, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results