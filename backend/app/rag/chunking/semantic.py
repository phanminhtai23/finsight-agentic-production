"""Semantic chunking — split text at semantic boundaries instead of fixed sizes.

Sentences are embedded and adjacent similarity is measured; a boundary is placed where
similarity drops below a percentile threshold. Requires an ``Embedder`` (injected), so it is
tested with a fake embedder.
"""

import math
import re

from app.rag.ports import Embedder

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * pct
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return ordered[int(k)]
    return ordered[lo] * (hi - k) + ordered[hi] * (k - lo)


class SemanticChunker:
    def __init__(
        self, embedder: Embedder, *, breakpoint_percentile: float = 0.25, max_chars: int = 1000
    ) -> None:
        self._embedder = embedder
        self._pct = breakpoint_percentile
        self._max_chars = max_chars

    async def split(self, text: str) -> list[str]:
        sentences = [s.strip() for s in _SENTENCE_RE.split(text.strip()) if s.strip()]
        if len(sentences) <= 1:
            return [text.strip()] if text.strip() else []

        vectors = await self._embedder.embed_documents(sentences)
        sims = [_cosine(vectors[i], vectors[i + 1]) for i in range(len(vectors) - 1)]
        threshold = _percentile(sims, self._pct)

        chunks: list[str] = []
        cur = sentences[0]
        for i, sentence in enumerate(sentences[1:]):
            boundary = sims[i] < threshold
            too_big = len(cur) + len(sentence) + 1 > self._max_chars
            if boundary or too_big:
                chunks.append(cur)
                cur = sentence
            else:
                cur = f"{cur} {sentence}"
        if cur:
            chunks.append(cur)
        return chunks
