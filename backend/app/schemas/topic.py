"""Topic + usage DTOs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TopicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None = None
    created_at: datetime
    document_count: int = 0
    size_bytes: int = 0


class UrlDocumentRequest(BaseModel):
    url: str = Field(min_length=4)
    title: str | None = None


class UsageOut(BaseModel):
    used_bytes: int
    quota_bytes: int
    quota_mb: int
    percent: float
