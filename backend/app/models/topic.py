"""Topic model — a named data collection owned by a user.

Each topic maps to its own Qdrant collection, so a topic's documents are retrieved in
isolation. A conversation can be pinned to a topic to scope retrieval to that data.
"""

import uuid

from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Topic(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "topics"

    user_id: Mapped[uuid.UUID] = mapped_column(index=True)
    name: Mapped[str]
    description: Mapped[str | None] = mapped_column(default=None)
    qdrant_collection: Mapped[str] = mapped_column(unique=True)

    @staticmethod
    def collection_name(topic_id: uuid.UUID) -> str:
        return f"topic_{topic_id.hex}"
