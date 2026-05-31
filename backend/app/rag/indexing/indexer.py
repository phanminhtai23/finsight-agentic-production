"""Indexer — embeds leaf chunks and upserts them into Qdrant.

Only leaf chunks (and tables) get a vector; each leaf carries its parent's larger block in
the payload (``parent_content``) for small-to-big context expansion at retrieval time.
"""

import uuid
from collections.abc import Iterator

from qdrant_client import models

from app.rag.chunking.models import ChunkData
from app.rag.indexing.qdrant_store import QdrantVectorStore
from app.rag.ports import Embedder


def _batched(items: list[ChunkData], size: int) -> Iterator[list[ChunkData]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


class Indexer:
    def __init__(
        self, store: QdrantVectorStore, embedder: Embedder, *, batch_size: int = 64
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._batch_size = batch_size

    async def index(
        self,
        document_id: uuid.UUID,
        chunks: list[ChunkData],
        *,
        document_title: str | None = None,
        cloudinary_url: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> int:
        await self._store.ensure_collection()

        content_by_local = {c.local_id: c.content for c in chunks}
        leaves = [c for c in chunks if c.embed]

        points: list[models.PointStruct] = []
        for batch in _batched(leaves, self._batch_size):
            vectors = await self._embedder.embed_documents([c.text_to_embed for c in batch])
            for chunk, vector in zip(batch, vectors, strict=True):
                parent_content = (
                    content_by_local.get(chunk.parent_local_id)
                    if chunk.parent_local_id is not None
                    else None
                )
                points.append(
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={
                            "document_id": str(document_id),
                            "document_title": document_title,
                            "cloudinary_url": cloudinary_url,
                            "user_id": str(user_id) if user_id else None,
                            "content": chunk.content,
                            "parent_content": parent_content,
                            "page": chunk.page,
                            "section_title": chunk.section_title,
                            "is_table": chunk.is_table,
                        },
                    )
                )

        await self._store.upsert(points)
        return len(points)
