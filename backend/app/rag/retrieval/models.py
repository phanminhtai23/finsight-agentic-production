"""Retrieval data models."""

from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    score: float
    document_id: str
    document_title: str | None = None
    page: int | None = None
    section_title: str | None = None
    cloudinary_url: str | None = None
    is_table: bool = False
    # Larger surrounding block for small-to-big expansion (stored in the chunk's payload).
    parent_content: str | None = None
