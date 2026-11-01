# /utils/sorting.py


def compute_weighted_score(
    *,
    semantic_similarity: float,
    recency_score: float,
    last_accessed_score: float,
) -> float:
    """Compute final relevance per project rule:
    Relevance = 0.7*semantic_similarity + 0.2*recency_score + 0.1*last_accessed_score

    All inputs should be normalized to [0, 1].
    """
    # clamp
    s = max(0.0, min(1.0, semantic_similarity))
    r = max(0.0, min(1.0, recency_score))
    l = max(0.0, min(1.0, last_accessed_score))
    return round(0.7 * s + 0.2 * r + 0.1 * l, 12)
