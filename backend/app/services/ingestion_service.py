"""Ingestion orchestration: parse → chunk → embed → index (Qdrant) → mark ready.

A pure orchestrator that depends on injected collaborators (parsers, chunking, embedder,
vector store, document repo). Supports file ingestion and web-link (URL) ingestion.
"""

import asyncio
import re
import uuid
from collections.abc import Awaitable, Callable

import httpx

from app.models.document import DocumentStatus
from app.rag.chunking.models import ElementType, ParsedDocument, ParsedElement
from app.rag.chunking.pipeline import ChunkingConfig, ChunkingPipeline
from app.rag.indexing.indexer import Indexer
from app.rag.indexing.qdrant_store import QdrantVectorStore
from app.rag.ingestion.parsers import ParserRegistry
from app.rag.ports import Embedder, TextGenerator
from app.repositories.document_repository import DocumentRepository

ProgressCallback = Callable[[int, str], Awaitable[None]]


async def _noop(_pct: int, _msg: str) -> None:
    return None


async def fetch_page_text(url: str, max_chars: int = 50_000) -> str:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "FinSight/0.1"})
        resp.raise_for_status()
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", resp.text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:max_chars]


class IngestionService:
    def __init__(
        self,
        *,
        document_repo: DocumentRepository,
        vector_store: QdrantVectorStore,
        embedder: Embedder,
        parser_registry: ParserRegistry | None = None,
        text_generator: TextGenerator | None = None,
        chunking_config: ChunkingConfig | None = None,
    ) -> None:
        self._documents = document_repo
        self._store = vector_store
        self._embedder = embedder
        self._parsers = parser_registry or ParserRegistry()
        self._generator = text_generator
        self._chunking_config = chunking_config or ChunkingConfig()

    async def _index_parsed(
        self,
        document_id: uuid.UUID,
        parsed: ParsedDocument,
        *,
        on_progress: ProgressCallback,
        cloudinary_url: str | None,
        user_id: uuid.UUID | None,
    ) -> int:
        await on_progress(40, "Chunking")
        pipeline = ChunkingPipeline(self._chunking_config, generator=self._generator)
        chunks = await pipeline.run(parsed)

        await on_progress(70, "Embedding & indexing")
        await self._store.ensure_collection()
        await self._store.delete_by_document(str(document_id))  # idempotent re-ingest
        count = await Indexer(self._store, self._embedder).index(
            document_id,
            chunks,
            document_title=parsed.title,
            cloudinary_url=cloudinary_url,
            user_id=user_id,
        )
        await self._documents.set_status(
            document_id, DocumentStatus.READY, page_count=parsed.page_count
        )
        await on_progress(100, "Ready")
        return count

    async def ingest(
        self,
        *,
        document_id: uuid.UUID,
        local_path: str,
        title: str,
        on_progress: ProgressCallback = _noop,
    ) -> int:
        document = await self._documents.get(document_id)
        await on_progress(10, "Parsing document")
        parsed = await asyncio.to_thread(self._parsers.parse, local_path, title=title)
        return await self._index_parsed(
            document_id,
            parsed,
            on_progress=on_progress,
            cloudinary_url=document.cloudinary_url if document else None,
            user_id=document.user_id if document else None,
        )

    async def ingest_url(
        self,
        *,
        document_id: uuid.UUID,
        url: str,
        title: str,
        on_progress: ProgressCallback = _noop,
    ) -> tuple[int, int]:
        """Ingest a web page. Returns (chunk_count, content_size_bytes)."""
        document = await self._documents.get(document_id)
        await on_progress(10, "Fetching page")
        text = await fetch_page_text(url)
        parsed = ParsedDocument(
            title=title,
            file_type="url",
            elements=[ParsedElement(text=text, type=ElementType.TEXT)],
            page_count=1,
        )
        count = await self._index_parsed(
            document_id,
            parsed,
            on_progress=on_progress,
            cloudinary_url=url,
            user_id=document.user_id if document else None,
        )
        return count, len(text.encode("utf-8"))
