"""Hybrid retriever: vector + keyword search fused with RRF, then small-to-big expansion.

Depends on a ``SearchBackend`` protocol (satisfied by ``QdrantSearchBackend``) and an
``Embedder`` port, so it can be unit-tested with in-memory fakes.
"""

import uuid
from typing import Protocol

from app.rag.ports import Embedder, Reranker
from app.rag.retrieval.fusion import reciprocal_rank_fusion
from app.rag.retrieval.models import RetrievedChunk


class SearchBackend(Protocol):
    async def vector_search(
        self,
        embedding: list[float],
        *,
        k: int = 20,
        document_ids: list[uuid.UUID] | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[RetrievedChunk]: ...

    async def keyword_search(
        self,
        query: str,
        *,
        k: int = 20,
        document_ids: list[uuid.UUID] | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[RetrievedChunk]: ...


class HybridRetriever:
    def __init__(
        self,
        backend: SearchBackend,
        embedder: Embedder,
        *,
        reranker: Reranker | None = None,
        candidate_k: int = 20,
        top_k: int = 6,
        expand_parents: bool = True,
    ) -> None:
        self._backend = backend
        self._embedder = embedder
        self._reranker = reranker
        self._candidate_k = candidate_k
        self._top_k = top_k
        self._expand_parents = expand_parents

    async def retrieve(
        self,
        query: str,
        *,
        document_ids: list[uuid.UUID] | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[RetrievedChunk]:
        query_vec = await self._embedder.embed_query(query)
        vector_hits = await self._backend.vector_search(
            query_vec, k=self._candidate_k, document_ids=document_ids, user_id=user_id
        )
        keyword_hits = await self._backend.keyword_search(
            query, k=self._candidate_k, document_ids=document_ids, user_id=user_id
        )

        by_id: dict[str, RetrievedChunk] = {}
        for hit in (*vector_hits, *keyword_hits):
            by_id.setdefault(hit.chunk_id, hit)

        fused = reciprocal_rank_fusion(
            [[h.chunk_id for h in vector_hits], [h.chunk_id for h in keyword_hits]]
        )
        ranked = [by_id[cid] for cid, _ in fused]

        if self._reranker is not None and ranked:
            order = await self._reranker.rerank(
                query, [c.content for c in ranked], top_k=self._top_k
            )
            ranked = [ranked[i] for i, _ in order]

        top = ranked[: self._top_k]
        if self._expand_parents:
            for chunk in top:
                if chunk.parent_content:
                    chunk.content = chunk.parent_content
        return top
