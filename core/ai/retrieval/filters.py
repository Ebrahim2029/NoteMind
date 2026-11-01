

from typing import Iterable, List, Sequence, Tuple


def filter_by_threshold(
    pairs: Sequence[Tuple[str, float]],
    threshold: float = 0.82,
) -> List[Tuple[str, float]]:
    """Keep only (id, score) with score >= threshold."""
    return [(i, s) for i, s in pairs if s >= threshold]
