"""Unit test for semantic chunking using a fake embedder (no network)."""

from app.rag.chunking.semantic import SemanticChunker


class FakeEmbedder:
    """Embeds sentences into one of two clusters based on a keyword."""

    dim = 2

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] if "alpha" in t else [0.0, 1.0] for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0] if "alpha" in text else [0.0, 1.0]


async def test_semantic_chunker_splits_at_topic_change():
    text = "alpha one. alpha two. alpha three. beta one. beta two. beta three."
    chunks = await SemanticChunker(FakeEmbedder(), max_chars=1000).split(text)
    assert len(chunks) >= 2
    assert any("alpha" in c and "beta" not in c for c in chunks)


async def test_semantic_chunker_single_sentence():
    chunks = await SemanticChunker(FakeEmbedder()).split("only one sentence here")
    assert chunks == ["only one sentence here"]
