"""Qdrant-backed search operations for the HybridRetriever.

Provides the dense ``vector_search`` and a keyword ``keyword_search`` (full-text payload
filter). The HybridRetriever fuses the two with RRF. (A sparse-vector BM25 leg can be added
later for stronger keyword ranking.)
"""

import uuid

from qdrant_client import AsyncQdrantClient, models

from app.rag.retrieval.models import RetrievedChunk


class QdrantSearchBackend:
    def __init__(self, client: AsyncQdrantClient, *, collection: str) -> None:
        self._client = client
        self._collection = collection

    @staticmethod
    def _filter(
        document_ids: list[uuid.UUID] | None, user_id: uuid.UUID | None
    ) -> models.Filter | None:
        must: list[models.FieldCondition] = []
        if document_ids:
            must.append(
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchAny(any=[str(d) for d in document_ids]),
                )
            )
        if user_id is not None:
            must.append(
                models.FieldCondition(key="user_id", match=models.MatchValue(value=str(user_id)))
            )
        return models.Filter(must=must) if must else None

    @staticmethod
    def _to_retrieved(point: object, score: float) -> RetrievedChunk:
        payload = getattr(point, "payload", None) or {}
        return RetrievedChunk(
            chunk_id=str(point.id),
            content=payload.get("content", ""),
            score=score,
            document_id=payload.get("document_id", ""),
            document_title=payload.get("document_title"),
            page=payload.get("page"),
            section_title=payload.get("section_title"),
            cloudinary_url=payload.get("cloudinary_url"),
            is_table=payload.get("is_table", False),
            parent_content=payload.get("parent_content"),
        )

    async def vector_search(
        self,
        embedding: list[float],
        *,
        k: int = 20,
        document_ids: list[uuid.UUID] | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[RetrievedChunk]:
        result = await self._client.query_points(
            self._collection,
            query=embedding,
            limit=k,
            query_filter=self._filter(document_ids, user_id),
            with_payload=True,
        )
        return [self._to_retrieved(p, float(p.score)) for p in result.points]

    async def keyword_search(
        self,
        query: str,
        *,
        k: int = 20,
        document_ids: list[uuid.UUID] | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[RetrievedChunk]:
        must: list[models.FieldCondition] = [
            models.FieldCondition(key="content", match=models.MatchText(text=query))
        ]
        base = self._filter(document_ids, user_id)
        if base is not None:
            must.extend(base.must)
        points, _ = await self._client.scroll(
            self._collection,
            scroll_filter=models.Filter(must=must),
            limit=k,
            with_payload=True,
        )
        return [self._to_retrieved(p, 0.0) for p in points]
