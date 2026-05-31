"""Reciprocal Rank Fusion (RRF) for combining vector and keyword result lists.

Pure and generic over hashable ids — unit-testable without a database.
"""

from collections.abc import Hashable, Sequence
from typing import TypeVar

T = TypeVar("T", bound=Hashable)


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[T]], *, k: int = 60
) -> list[tuple[T, float]]:
    """Fuse several ranked id lists into one.

    Each list contributes ``1 / (k + rank)`` to an id's score. Higher score ranks first.
    ``k`` damps the influence of top ranks (60 is the canonical default).
    """
    scores: dict[T, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
