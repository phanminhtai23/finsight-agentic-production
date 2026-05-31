"""RAG ports (abstractions).

The RAG pipeline depends on these ``Protocol`` interfaces, not on concrete LLM SDKs.
Concrete adapters (Gemini) live in ``app.core.llm``; tests inject fakes. This keeps the
ingestion/retrieval logic decoupled and unit-testable (Dependency Inversion).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Embedder(Protocol):
    """Turns text into dense vectors."""

    dim: int

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


@runtime_checkable
class TextGenerator(Protocol):
    """Single-shot text generation (used by the contextualizer)."""

    async def generate(self, prompt: str) -> str: ...


@runtime_checkable
class Reranker(Protocol):
    """Reorders candidate passages by relevance to a query."""

    async def rerank(
        self, query: str, passages: list[str], *, top_k: int
    ) -> list[tuple[int, float]]:
        """Return ``(original_index, score)`` pairs, best first."""
        ...
