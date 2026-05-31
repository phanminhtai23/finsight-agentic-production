"""Topic lifecycle — keeps the Postgres rows and the per-topic Qdrant collection in sync."""

from qdrant_client import AsyncQdrantClient

from app.core.config import Settings
from app.models.document import Document
from app.models.topic import Topic
from app.models.user import User
from app.rag.indexing.qdrant_store import QdrantVectorStore
from app.repositories.document_repository import DocumentRepository
from app.repositories.topic_repository import TopicRepository


class TopicService:
    def __init__(
        self,
        topics: TopicRepository,
        documents: DocumentRepository,
        qdrant: AsyncQdrantClient,
        settings: Settings,
    ) -> None:
        self._topics = topics
        self._documents = documents
        self._qdrant = qdrant
        self._settings = settings

    def _store(self, collection: str) -> QdrantVectorStore:
        return QdrantVectorStore(
            self._qdrant, collection=collection, dim=self._settings.embedding_dim
        )

    async def create(self, *, user_id, name: str, description: str | None) -> Topic:
        topic = await self._topics.create(user_id=user_id, name=name, description=description)
        await self._store(topic.qdrant_collection).ensure_collection()
        return topic

    async def delete_topic(self, topic: Topic, user: User) -> None:
        docs = await self._documents.list_by_topic(topic.id)
        freed = sum(d.size_bytes or 0 for d in docs)
        await self._store(topic.qdrant_collection).delete_collection()
        await self._topics.delete(topic)  # cascades to document rows
        user.storage_used_bytes = max(0, (user.storage_used_bytes or 0) - freed)

    async def delete_document(self, document: Document, topic: Topic, user: User) -> None:
        await self._store(topic.qdrant_collection).delete_by_document(str(document.id))
        freed = document.size_bytes or 0
        await self._documents.delete(document)
        user.storage_used_bytes = max(0, (user.storage_used_bytes or 0) - freed)
