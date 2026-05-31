"""Web search port for the Market Research agent.

A real implementation is provided in M3 via the MCP server. Until then the default is a
no-op so the graph runs end-to-end on document-only questions.
"""

from typing import Protocol, runtime_checkable

from app.agents.state import EvidenceItem


@runtime_checkable
class WebSearch(Protocol):
    async def search(self, query: str, *, k: int = 5) -> list[EvidenceItem]: ...


class NullWebSearch:
    """Returns nothing — live web research is wired in M3 (MCP)."""

    async def search(self, query: str, *, k: int = 5) -> list[EvidenceItem]:
        return []
