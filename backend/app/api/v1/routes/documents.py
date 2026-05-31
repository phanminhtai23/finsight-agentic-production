"""Document upload + status endpoints."""

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
from app.rag.ingestion.storage import get_file_storage
from app.schemas.document import DocumentOut, DocumentUploadResponse

router = APIRouter()


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    session: SessionDep,
    settings: SettingsDep,
    document_repo: DocumentRepoDep,
    task_repo: TaskRepoDep,
    arq: ArqDep,
    file: Annotated[UploadFile, File()],
) -> DocumentUploadResponse:
    """Upload a document; raw file is stored and async ingestion is enqueued."""
    suffix = Path(file.filename or "upload").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Store the raw file; the worker (a separate process) re-fetches it from this URL.
    public_id, url = await get_file_storage(settings).upload(tmp_path)
    os.unlink(tmp_path)

    document = Document(
        title=file.filename or Path(tmp_path).name,
        file_type=(suffix.lstrip(".").lower() or "bin"),
        cloudinary_public_id=public_id,
        cloudinary_url=url,
        status=DocumentStatus.PROCESSING,
    )
    await document_repo.add(document)
    task = await task_repo.create(type=TaskType.INGESTION, input={"document_id": str(document.id)})
    # Commit before enqueuing so the worker can read a persisted task/document.
    await session.commit()

    await arq.enqueue_job("ingest_document", str(task.id), str(document.id))
    return DocumentUploadResponse(document=DocumentOut.model_validate(document), task_id=task.id)


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: uuid.UUID, document_repo: DocumentRepoDep) -> DocumentOut:
    document = await document_repo.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut.model_validate(document)


@router.get("", response_model=list[DocumentOut])
async def list_documents(document_repo: DocumentRepoDep) -> list[DocumentOut]:
    return [DocumentOut.model_validate(d) for d in await document_repo.list()]


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    user: CurrentUserDep,
    document_repo: DocumentRepoDep,
    topic_repo: TopicRepoDep,
    topic_service: TopicServiceDep,
    session: SessionDep,
) -> None:
    document = await document_repo.get(document_id)
    if document is None or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.topic_id is None:
        raise HTTPException(status_code=400, detail="Document is not attached to a topic")
    topic = await topic_repo.get(document.topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    await topic_service.delete_document(document, topic, user)
    await session.commit()
