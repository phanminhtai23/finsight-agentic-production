"""Question-answering DTOs."""

import uuid

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    document_ids: list[uuid.UUID] | None = None


class CitationOut(BaseModel):
    index: int
    document_id: str
    document_title: str | None = None
    page: int | None = None
    url: str | None = None
    snippet: str


class AnswerOut(BaseModel):
    answer: str
    citations: list[CitationOut]
