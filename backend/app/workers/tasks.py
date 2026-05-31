"""ARQ task functions (run in the background worker)."""

import os
import tempfile
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import httpx

from app.core.cache import create_redis_pool
from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.core.llm import get_embedder, get_text_generator
from app.core.qdrant import get_qdrant_client
from app.models.document import DocumentStatus
from app.models.task import TaskStatus
from app.models.topic import Topic
from app.models.user import User
from app.rag.indexing.qdrant_store import QdrantVectorStore
from app.repositories.document_repository import DocumentRepository
from app.repositories.task_repository import TaskRepository
from app.services.events import EventPublisher
from app.services.ingestion_service import IngestionService


async def _fetch_to_temp(url: str, suffix: str) -> str:
    """Download the source file (http(s) or file://) to a local temp path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    if url.startswith(("http://", "https://")):
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            Path(path).write_bytes(resp.content)
    elif url.startswith("file://"):
        src = unquote(urlparse(url).path).lstrip("/")
        Path(path).write_bytes(Path(src).read_bytes())
    else:
        Path(path).write_bytes(Path(url).read_bytes())
    return path


async def ingest_document(ctx: dict[str, Any], task_id: str, document_id: str) -> dict:
    """Fetch → parse → chunk → embed → index a document, streaming progress over Redis."""
    settings = get_settings()
    redis_client = create_redis_pool(settings)
    publisher = EventPublisher(redis_client)
    sessionmaker = get_sessionmaker()
    tid, did = uuid.UUID(task_id), uuid.UUID(document_id)
    local_path: str | None = None

    async with sessionmaker() as session:
        documents = DocumentRepository(session)
        tasks = TaskRepository(session)

        async def on_progress(pct: int, message: str) -> None:
            await tasks.update(tid, status=TaskStatus.RUNNING, progress=pct)
            await session.commit()
            await publisher.publish_task(task_id, status="running", progress=pct, message=message)

        try:
            document = await documents.get(did)
            if document is None:
                raise RuntimeError("Document not found")

            # Resolve the target Qdrant collection (per-topic, else default).
            collection = settings.qdrant_collection
            if document.topic_id:
                topic = await session.get(Topic, document.topic_id)
                if topic:
                    collection = topic.qdrant_collection
            store = QdrantVectorStore(
                get_qdrant_client(settings), collection=collection, dim=settings.embedding_dim
            )
            service = IngestionService(
                document_repo=documents,
                vector_store=store,
                embedder=get_embedder(),
                text_generator=get_text_generator(),
            )

            if document.source_type == "url":
                count, size = await service.ingest_url(
                    document_id=did,
                    url=document.source_url,
                    title=document.title,
                    on_progress=on_progress,
                )
                document.size_bytes = size
                if document.user_id:  # account web-page size against the user's quota
                    user = await session.get(User, document.user_id)
                    if user:
                        user.storage_used_bytes = (user.storage_used_bytes or 0) + size
            else:
                if not document.cloudinary_url:
                    raise RuntimeError("Document has no source URL")
                await on_progress(5, "Fetching source file")
                local_path = await _fetch_to_temp(document.cloudinary_url, f".{document.file_type}")
                count = await service.ingest(
                    document_id=did,
                    local_path=local_path,
                    title=document.title,
                    on_progress=on_progress,
                )

            await tasks.update(
                tid, status=TaskStatus.SUCCEEDED, progress=100, result={"chunks": count}
            )
            await session.commit()
            await publisher.publish_task(
                task_id, status="succeeded", progress=100, result={"chunks": count}
            )
            return {"chunks": count}
        except Exception as exc:
            await session.rollback()
            await documents.set_status(did, DocumentStatus.FAILED, error=str(exc))
            await tasks.update(tid, status=TaskStatus.FAILED, error=str(exc))
            await session.commit()
            await publisher.publish_task(task_id, status="failed", progress=100, message=str(exc))
            raise
        finally:
            await redis_client.aclose()
            if local_path:
                Path(local_path).unlink(missing_ok=True)
