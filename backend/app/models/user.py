"""User model."""

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(default=None)  # null for OAuth-only
    full_name: Mapped[str | None] = mapped_column(default=None)
    avatar_url: Mapped[str | None] = mapped_column(default=None)
    is_verified: Mapped[bool] = mapped_column(default=False)
    auth_provider: Mapped[str] = mapped_column(default="password")  # "password" | "google"
    tier: Mapped[str] = mapped_column(default="free")  # "free" | "pro" | "pro_max"
    storage_used_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
