"""Conversation and Message models.

NOTE: LangGraph also persists per-thread state via its PostgresSaver/PostgresStore. These
tables hold the application-facing chat record (for listing, display, and citations); they
complement — not replace — the LangGraph checkpoint tables.
"""

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Conversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID | None] = mapped_column(default=None, index=True)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), default=None, index=True
    )
    title: Mapped[str | None] = mapped_column(default=None)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str]  # "user" | "assistant" | "system"
    content: Mapped[str]
    citations: Mapped[list | None] = mapped_column(JSONB, default=None)
    charts: Mapped[list | None] = mapped_column(JSONB, default=None)
    tools: Mapped[list | None] = mapped_column(JSONB, default=None)  # tool names the agent used

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
