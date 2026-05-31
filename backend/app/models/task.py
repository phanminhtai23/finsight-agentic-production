"""Task model — a long-running background job (ingestion / deep research).

Tasks let a conversation run heavy work in the background (via ARQ) while the user keeps
chatting. Progress is streamed over Redis pub/sub → WebSocket.
"""

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class TaskType(enum.StrEnum):
    INGESTION = "ingestion"
    RESEARCH = "research"


class TaskStatus(enum.StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Task(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks"

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), default=None, index=True
    )
    type: Mapped[TaskType] = mapped_column(
        SAEnum(TaskType, name="task_type", values_callable=lambda e: [m.value for m in e])
    )
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(
            TaskStatus,
            name="task_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=TaskStatus.QUEUED,
    )
    progress: Mapped[int] = mapped_column(default=0)  # 0..100
    input: Mapped[dict | None] = mapped_column(JSONB, default=None)
    result: Mapped[dict | None] = mapped_column(JSONB, default=None)
    error: Mapped[str | None] = mapped_column(default=None)
