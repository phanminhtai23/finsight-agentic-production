"""Data access for documents."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.flush()
        return document

    async def get(self, document_id: uuid.UUID) -> Document | None:
        return await self.session.get(Document, document_id)

    async def list(self, *, user_id: uuid.UUID | None = None, limit: int = 50) -> list[Document]:
        stmt = select(Document).order_by(Document.created_at.desc()).limit(limit)
        if user_id is not None:
            stmt = stmt.where(Document.user_id == user_id)
        return list((await self.session.scalars(stmt)).all())

    async def list_by_topic(self, topic_id: uuid.UUID) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.topic_id == topic_id)
            .order_by(Document.created_at.desc())
        )
        return list((await self.session.scalars(stmt)).all())

    async def delete(self, document: Document) -> None:
        await self.session.delete(document)

    async def set_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        *,
        error: str | None = None,
        page_count: int | None = None,
    ) -> None:
        doc = await self.session.get(Document, document_id)
        if doc is None:
            return
        doc.status = status
        if error is not None:
            doc.error = error
        if page_count is not None:
            doc.page_count = page_count
