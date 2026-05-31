"""Build citation records from retrieved evidence.

Citations are numbered ``[1..n]`` in the order evidence is presented to the Writer, so the
inline markers it emits map deterministically back to source pages.
"""

from dataclasses import dataclass

from app.rag.retrieval.models import RetrievedChunk

_SNIPPET_CHARS = 240


@dataclass
class Citation:
    index: int
    document_id: str
    document_title: str | None
    page: int | None
    url: str | None
    snippet: str

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "document_id": self.document_id,
            "document_title": self.document_title,
            "page": self.page,
            "url": self.url,
            "snippet": self.snippet,
        }


def build_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    citations: list[Citation] = []
    for i, chunk in enumerate(chunks, start=1):
        snippet = chunk.content.strip().replace("\n", " ")
        if len(snippet) > _SNIPPET_CHARS:
            snippet = snippet[:_SNIPPET_CHARS].rstrip() + "…"
        citations.append(
            Citation(
                index=i,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                page=chunk.page,
                url=chunk.cloudinary_url,
                snippet=snippet,
            )
        )
    return citations


def format_sources_block(citations: list[Citation]) -> str:
    """Render a human-readable Sources list for appending to an answer."""
    lines = ["Sources:"]
    for c in citations:
        loc = f" — p.{c.page}" if c.page is not None else ""
        title = c.document_title or c.document_id
        url = f"  {c.url}" if c.url else ""
        lines.append(f"[{c.index}] {title}{loc}{url}")
    return "\n".join(lines)
