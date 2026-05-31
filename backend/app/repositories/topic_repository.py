"""Data access for topics."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.topic import Topic


class TopicRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, user_id: uuid.UUID, name: str, description: str | None) -> Topic:
        topic = Topic(user_id=user_id, name=name, description=description, qdrant_collection="")
        self.session.add(topic)
        await self.session.flush()
        topic.qdrant_collection = Topic.collection_name(topic.id)
        return topic

    async def get(self, topic_id: uuid.UUID) -> Topic | None:
        return await self.session.get(Topic, topic_id)

    async def get_owned(self, topic_id: uuid.UUID, user_id: uuid.UUID) -> Topic | None:
        topic = await self.session.get(Topic, topic_id)
        return topic if topic and topic.user_id == user_id else None

    async def list_for_user(self, user_id: uuid.UUID) -> list[tuple[Topic, int, int]]:
        """Return (topic, document_count, total_size_bytes) for a user's topics."""
        stmt = (
            select(
                Topic,
                func.count(Document.id),
                func.coalesce(func.sum(Document.size_bytes), 0),
            )
            .outerjoin(Document, Document.topic_id == Topic.id)
            .where(Topic.user_id == user_id)
            .group_by(Topic.id)
            .order_by(Topic.created_at.desc())
        )
        rows = (await self.session.execute(stmt)).all()
        return [(t, int(count), int(size)) for t, count, size in rows]

    async def delete(self, topic: Topic) -> None:
        await self.session.delete(topic)
