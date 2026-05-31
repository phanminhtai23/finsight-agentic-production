"""Unit test for HybridRetriever using in-memory fakes (no Qdrant)."""

import uuid

from app.rag.retrieval.hybrid import HybridRetriever
from app.rag.retrieval.models import RetrievedChunk

ID_A = str(uuid.uuid4())
ID_B = str(uuid.uuid4())
ID_C = str(uuid.uuid4())


def _chunk(cid: str, content: str, parent: str | None = None) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=cid, content=content, score=1.0, document_id="doc", parent_content=parent
    )


class FakeEmbedder:
    dim = 1

    async def embed_documents(self, texts):
        return [[1.0] for _ in texts]

    async def embed_query(self, text):
        return [1.0]


class FakeBackend:
    def __init__(self, vector, keyword):
        self._vector, self._keyword = vector, keyword

    async def vector_search(self, embedding, *, k=20, document_ids=None, user_id=None):
        return self._vector

    async def keyword_search(self, query, *, k=20, document_ids=None, user_id=None):
        return self._keyword


async def test_hybrid_fuses_and_expands_to_parent():
    vector = [_chunk(ID_A, "child A"), _chunk(ID_B, "child B", parent="PARENT CONTEXT for B")]
    keyword = [_chunk(ID_B, "child B", parent="PARENT CONTEXT for B"), _chunk(ID_C, "child C")]

    retriever = HybridRetriever(FakeBackend(vector, keyword), FakeEmbedder(), top_k=3)
    results = await retriever.retrieve("q")

    ids = [r.chunk_id for r in results]
    assert ids[0] == ID_B  # appears in both lists → fused to the top
    assert set(ids) == {ID_A, ID_B, ID_C}
    # child B's content was expanded to its parent's larger context
    b = next(r for r in results if r.chunk_id == ID_B)
    assert b.content == "PARENT CONTEXT for B"
