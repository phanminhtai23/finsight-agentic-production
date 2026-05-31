"""Health DTOs."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str
    version: str
