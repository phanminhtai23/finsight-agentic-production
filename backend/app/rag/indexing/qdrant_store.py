"""Qdrant vector store — collection lifecycle and upserts.

Holds chunk embeddings + denormalized payload (content, parent context, citation metadata).
A keyword (full-text) payload index on ``content`` enables the hybrid retriever's keyword leg.
"""

from qdrant_client import AsyncQdrantClient, models


class QdrantVectorStore:
    def __init__(self, client: AsyncQdrantClient, *, collection: str, dim: int) -> None:
        self._client = client
        self._collection = collection
        self._dim = dim

    async def ensure_collection(self) -> None:
        if await self._client.collection_exists(self._collection):
            return
        await self._client.create_collection(
            collection_name=self._collection,
            vectors_config=models.VectorParams(size=self._dim, distance=models.Distance.COSINE),
        )
        await self._client.create_payload_index(
            self._collection, "document_id", models.PayloadSchemaType.KEYWORD
        )
        await self._client.create_payload_index(
            self._collection,
            "content",
            models.TextIndexParams(
                type=models.TextIndexType.TEXT,
                tokenizer=models.TokenizerType.WORD,
                min_token_len=2,
                lowercase=True,
            ),
        )

    async def upsert(self, points: list[models.PointStruct]) -> None:
        if points:
            await self._client.upsert(self._collection, points=points)

    async def delete_collection(self) -> None:
        if await self._client.collection_exists(self._collection):
            await self._client.delete_collection(self._collection)

    async def delete_by_document(self, document_id: str) -> None:
        await self._client.delete(
            self._collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id", match=models.MatchValue(value=document_id)
                        )
                    ]
                )
            ),
        )
