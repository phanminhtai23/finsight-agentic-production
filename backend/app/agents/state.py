"""Shared LangGraph state for the multi-agent graph.

Kept JSON-serializable (plain dicts/lists/primitives) so the Postgres checkpointer can
persist and resume each conversation thread.
"""

from operator import add
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage


class EvidenceItem(TypedDict, total=False):
    content: str
    document_id: str
    document_title: str | None
    page: int | None
    url: str | None
    source: str  # "documents" | "web"


class CitationItem(TypedDict, total=False):
    index: int
    document_id: str
    document_title: str | None
    page: int | None
    url: str | None
    snippet: str


class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add]
    question: str
    collection: str | None  # topic's Qdrant collection to retrieve from (None = skip RAG)
    needs_web: bool
    evidence: list[EvidenceItem]
    analysis: str
    answer: str
    citations: list[CitationItem]
    critique: str
    approved: bool
    revisions: int
