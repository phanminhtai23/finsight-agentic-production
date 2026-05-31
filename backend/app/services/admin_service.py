"""Admin service — user analytics and destructive user management.

Aggregates dashboard stats with a few grouped queries and deletes a user together with all of
their data: per-topic Qdrant collections, documents, conversations and messages.
"""

import uuid

from qdrant_client import AsyncQdrantClient
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.logging import get_logger
from app.models.conversation import Conversation, Message
from app.models.document import Document
from app.models.topic import Topic
from app.models.user import User
from app.rag.indexing.qdrant_store import QdrantVectorStore
from app.schemas.admin import AdminStats, AdminUserOut, DayCount

log = get_logger(__name__)


class AdminError(Exception):
    """Raised on an invalid admin operation (mapped to 400/404 at the API layer)."""


class AdminService:
    def __init__(
        self, session: AsyncSession, qdrant: AsyncQdrantClient, settings: Settings
    ) -> None:
        self._session = session
        self._qdrant = qdrant
        self._settings = settings

    async def list_users(self) -> list[AdminUserOut]:
        # Correlated scalar subqueries keep this to a single round trip.
        doc_c = select(func.count()).where(Document.user_id == User.id).scalar_subquery()
        conv_c = select(func.count()).where(Conversation.user_id == User.id).scalar_subquery()
        msg_c = (
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == User.id, Message.role == "user")
            .scalar_subquery()
        )
        stmt = select(User, doc_c, conv_c, msg_c).order_by(User.created_at.desc())
        rows = (await self._session.execute(stmt)).all()
        return [
            AdminUserOut(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                avatar_url=u.avatar_url,
                is_verified=u.is_verified,
                is_admin=u.is_admin,
                auth_provider=u.auth_provider,
                tier=u.tier,
                storage_used_bytes=u.storage_used_bytes or 0,
                document_count=int(docs or 0),
                conversation_count=int(convs or 0),
                message_count=int(msgs or 0),
                created_at=u.created_at,
            )
            for u, docs, convs, msgs in rows
        ]

    async def _count(self, stmt) -> int:
        return int((await self._session.scalar(stmt)) or 0)

    async def _group_counts(self, column) -> dict[str, int]:
        stmt = select(column, func.count()).group_by(column)
        return {str(k): int(v) for k, v in (await self._session.execute(stmt)).all()}

    async def _by_day(self, created_at_col, *, where=None, limit_days: int = 30) -> list[DayCount]:
        day = func.date(created_at_col).label("day")
        stmt = select(day, func.count()).group_by(day).order_by(day)
        if where is not None:
            stmt = stmt.where(where)
        rows = (await self._session.execute(stmt)).all()
        out = [DayCount(date=str(d), count=int(c)) for d, c in rows]
        return out[-limit_days:]

    async def stats(self) -> AdminStats:
        total_users = await self._count(select(func.count()).select_from(User))
        verified = await self._count(
            select(func.count()).select_from(User).where(User.is_verified.is_(True))
        )
        admins = await self._count(
            select(func.count()).select_from(User).where(User.is_admin.is_(True))
        )
        total_docs = await self._count(select(func.count()).select_from(Document))
        total_convs = await self._count(select(func.count()).select_from(Conversation))
        total_msgs = await self._count(
            select(func.count()).select_from(Message).where(Message.role == "user")
        )
        total_storage = await self._count(
            select(func.coalesce(func.sum(User.storage_used_bytes), 0))
        )

        return AdminStats(
            total_users=total_users,
            verified_users=verified,
            unverified_users=total_users - verified,
            admin_users=admins,
            total_documents=total_docs,
            total_conversations=total_convs,
            total_messages=total_msgs,
            total_storage_bytes=total_storage,
            tier_distribution=await self._group_counts(User.tier),
            provider_distribution=await self._group_counts(User.auth_provider),
            signups_by_day=await self._by_day(User.created_at),
            messages_by_day=await self._by_day(Message.created_at, where=Message.role == "user"),
        )

    async def delete_user(self, user_id: uuid.UUID, *, requester_id: uuid.UUID) -> None:
        if user_id == requester_id:
            raise AdminError("You cannot delete your own admin account.")
        user = await self._session.get(User, user_id)
        if user is None:
            raise AdminError("User not found")

        # Drop each topic's Qdrant collection, then the topic row (cascades document rows).
        topics = (await self._session.scalars(select(Topic).where(Topic.user_id == user_id))).all()
        for topic in topics:
            try:
                store = QdrantVectorStore(
                    self._qdrant,
                    collection=topic.qdrant_collection,
                    dim=self._settings.embedding_dim,
                )
                await store.delete_collection()
            except Exception as exc:  # noqa: BLE001 - best effort; keep deleting the rest
                log.warning(
                    "admin_qdrant_delete_failed", collection=topic.qdrant_collection, error=str(exc)
                )
            await self._session.delete(topic)

        # Any topic-less documents, then conversations (messages cascade), then the user.
        await self._session.execute(delete(Document).where(Document.user_id == user_id))
        await self._session.execute(delete(Conversation).where(Conversation.user_id == user_id))
        await self._session.delete(user)
        log.info("admin_deleted_user", user_id=str(user_id), topics=len(topics))
