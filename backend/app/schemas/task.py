"""Task DTOs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    status: str
    progress: int
    conversation_id: uuid.UUID | None = None
    result: dict | None = None
    error: str | None = None
    created_at: datetime
