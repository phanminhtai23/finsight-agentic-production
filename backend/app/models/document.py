"""Document model — a user-uploaded source file (PDF / DOCX / image)."""

import enum
import uuid

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class DocumentStatus(enum.StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID | None] = mapped_column(default=None, index=True)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), default=None, index=True
    )
    title: Mapped[str]
    file_type: Mapped[str]
    source_type: Mapped[str] = mapped_column(default="file")  # "file" | "url"
    source_url: Mapped[str | None] = mapped_column(default=None)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    company: Mapped[str | None] = mapped_column(default=None, index=True)
    fiscal_period: Mapped[str | None] = mapped_column(default=None)

    cloudinary_public_id: Mapped[str | None] = mapped_column(default=None)
    cloudinary_url: Mapped[str | None] = mapped_column(default=None)

    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(
            DocumentStatus,
            name="document_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=DocumentStatus.PROCESSING,
    )
    page_count: Mapped[int | None] = mapped_column(default=None)
    error: Mapped[str | None] = mapped_column(default=None)
    # Chunks/embeddings live in Qdrant (see app.rag.indexing.qdrant_store), not Postgres.
