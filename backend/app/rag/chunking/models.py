"""Data models shared across parsing → chunking → indexing.

Plain dataclasses (no DB / no LLM) so the chunking logic stays pure and unit-testable.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class ElementType(StrEnum):
    HEADING = "heading"
    TEXT = "text"
    TABLE = "table"


@dataclass
class ParsedElement:
    """A located piece of content extracted from a source document."""

    text: str
    type: ElementType = ElementType.TEXT
    page: int | None = None
    bbox: dict | None = None  # {"x0","y0","x1","y1"}
    section_title: str | None = None


@dataclass
class ParsedDocument:
    title: str
    file_type: str
    elements: list[ParsedElement] = field(default_factory=list)
    page_count: int | None = None


@dataclass
class ChunkData:
    """A chunk ready to embed and persist.

    ``local_id`` / ``parent_local_id`` express the parent-child link positionally so the
    chunker stays DB-agnostic; the indexing layer maps them to real foreign keys.
    """

    content: str
    local_id: int
    parent_local_id: int | None = None
    contextualized_content: str | None = None
    page: int | None = None
    bbox: dict | None = None
    section_title: str | None = None
    is_table: bool = False
    # Small-to-big: parent (context-only) chunks are not embedded; only leaves/tables are.
    embed: bool = True
    extra_metadata: dict | None = None

    @property
    def text_to_embed(self) -> str:
        """Prefer the contextualized form (Anthropic contextual retrieval) when present."""
        return self.contextualized_content or self.content
