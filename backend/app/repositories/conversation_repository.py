"""Data access for conversations and messages."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID | None = None,
        title: str | None = None,
        topic_id: uuid.UUID | None = None,
    ) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title, topic_id=topic_id)
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get(self, conversation_id: uuid.UUID) -> Conversation | None:
        return await self.session.get(Conversation, conversation_id)

    async def list_for_user(self, user_id: uuid.UUID) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
        )
        return list((await self.session.scalars(stmt)).all())

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        *,
        role: str,
        content: str,
        citations: list | None = None,
        charts: list | None = None,
        tools: list | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations,
            charts=charts,
            tools=tools,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def list_messages(self, conversation_id: uuid.UUID) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list((await self.session.scalars(stmt)).all())
