"""Admin DTOs — user management and dashboard analytics."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class AdminUserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None = None
    avatar_url: str | None = None
    is_verified: bool
    is_admin: bool
    auth_provider: str
    tier: str
    storage_used_bytes: int
    document_count: int
    conversation_count: int
    message_count: int  # user-authored messages ≈ number of requests/queries
    created_at: datetime


class DayCount(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class AdminStats(BaseModel):
    total_users: int
    verified_users: int
    unverified_users: int
    admin_users: int
    total_documents: int
    total_conversations: int
    total_messages: int
    total_storage_bytes: int
    tier_distribution: dict[str, int]
    provider_distribution: dict[str, int]
    signups_by_day: list[DayCount]
    messages_by_day: list[DayCount]
