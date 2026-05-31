"""Topic + per-topic document endpoints (auth required, user-scoped)."""

import os
import tempfile
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.deps import (
    ArqDep,
    CurrentUserDep,
    DocumentRepoDep,
    SessionDep,
    SettingsDep,
    TaskRepoDep,
    TopicRepoDep,
    TopicServiceDep,
)
from app.models.document import Document, DocumentStatus
from app.models.task import TaskType
from app.models.topic import Topic
from app.models.user import User
from app.rag.ingestion.storage import get_file_storage
from app.schemas.document import DocumentOut, DocumentUploadResponse
from app.schemas.topic import TopicCreate, TopicOut, UrlDocumentRequest

router = APIRouter()


def _ensure_quota(user: User, add_bytes: int, settings) -> None:  # noqa: ANN001
    quota = settings.storage_quota_mb * 1024 * 1024
    if (user.storage_used_bytes or 0) + add_bytes > quota:
        raise HTTPException(
            status_code=413,
            detail=f"Storage quota exceeded (limit {settings.storage_quota_mb} MB)",
        )


async def _require_topic(topic_repo: TopicRepoDep, topic_id: uuid.UUID, user: User) -> Topic:
    topic = await topic_repo.get_owned(topic_id, user.id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("", response_model=TopicOut, status_code=201)
async def create_topic(
    body: TopicCreate, user: CurrentUserDep, service: TopicServiceDep, session: SessionDep
) -> TopicOut:
    topic = await service.create(user_id=user.id, name=body.name, description=body.description)
    await session.commit()
    return TopicOut(
        id=topic.id,
        name=topic.name,
        description=topic.description,
        created_at=topic.created_at,
    )


@router.get("", response_model=list[TopicOut])
async def list_topics(user: CurrentUserDep, topic_repo: TopicRepoDep) -> list[TopicOut]:
    return [
        TopicOut(
            id=t.id,
            name=t.name,
            description=t.description,
            created_at=t.created_at,
            document_count=count,
            size_bytes=size,
        )
        for t, count, size in await topic_repo.list_for_user(user.id)
    ]


@router.delete("/{topic_id}", status_code=204)
async def delete_topic(
    topic_id: uuid.UUID,
    user: CurrentUserDep,
    service: TopicServiceDep,
    topic_repo: TopicRepoDep,
    session: SessionDep,
) -> None:
    topic = await _require_topic(topic_repo, topic_id, user)
    await service.delete_topic(topic, user)
    await session.commit()


@router.get("/{topic_id}/documents", response_model=list[DocumentOut])
async def list_documents(
    topic_id: uuid.UUID,
    user: CurrentUserDep,
    topic_repo: TopicRepoDep,
    document_repo: DocumentRepoDep,
) -> list[DocumentOut]:
    await _require_topic(topic_repo, topic_id, user)
    return [DocumentOut.model_validate(d) for d in await document_repo.list_by_topic(topic_id)]


@router.post("/{topic_id}/documents", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    topic_id: uuid.UUID,
    user: CurrentUserDep,
    settings: SettingsDep,
    topic_repo: TopicRepoDep,
    document_repo: DocumentRepoDep,
    task_repo: TaskRepoDep,
    arq: ArqDep,
    session: SessionDep,
    file: Annotated[UploadFile, File()],
) -> DocumentUploadResponse:
    topic = await _require_topic(topic_repo, topic_id, user)
    data = await file.read()
    size = len(data)
    _ensure_quota(user, size, settings)

    suffix = Path(file.filename or "upload").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    public_id, url = await get_file_storage(settings).upload(tmp_path)
    os.unlink(tmp_path)

    document = Document(
        user_id=user.id,
        topic_id=topic.id,
        title=file.filename or Path(tmp_path).name,
        file_type=(suffix.lstrip(".").lower() or "bin"),
        source_type="file",
        size_bytes=size,
        cloudinary_public_id=public_id,
        cloudinary_url=url,
        status=DocumentStatus.PROCESSING,
    )
    await document_repo.add(document)
    user.storage_used_bytes = (user.storage_used_bytes or 0) + size
    task = await task_repo.create(type=TaskType.INGESTION, input={"document_id": str(document.id)})
    await session.commit()
    await arq.enqueue_job("ingest_document", str(task.id), str(document.id))
    return DocumentUploadResponse(document=DocumentOut.model_validate(document), task_id=task.id)


@router.post("/{topic_id}/documents/url", response_model=DocumentUploadResponse, status_code=201)
async def add_url_document(
    topic_id: uuid.UUID,
    body: UrlDocumentRequest,
    user: CurrentUserDep,
    topic_repo: TopicRepoDep,
    document_repo: DocumentRepoDep,
    task_repo: TaskRepoDep,
    arq: ArqDep,
    session: SessionDep,
) -> DocumentUploadResponse:
    topic = await _require_topic(topic_repo, topic_id, user)
    document = Document(
        user_id=user.id,
        topic_id=topic.id,
        title=body.title or body.url,
        file_type="url",
        source_type="url",
        source_url=body.url,
        size_bytes=0,
        status=DocumentStatus.PROCESSING,
    )
    await document_repo.add(document)
    task = await task_repo.create(type=TaskType.INGESTION, input={"document_id": str(document.id)})
    await session.commit()
    await arq.enqueue_job("ingest_document", str(task.id), str(document.id))
    return DocumentUploadResponse(document=DocumentOut.model_validate(document), task_id=task.id)
