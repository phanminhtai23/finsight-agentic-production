"""Application configuration loaded from environment variables.

Centralizing settings here (and injecting them) keeps modules free of direct
``os.environ`` access — supporting the Dependency Inversion principle.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "FinSight"
    environment: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173"]

    # --- Datastores ---
    database_url: str = Field(
        default="postgresql+asyncpg://finsight:finsight@localhost:5432/finsight",
        description="Async SQLAlchemy/asyncpg DSN for the application tables.",
    )
    # LangGraph's PostgresSaver/Store uses a sync psycopg DSN.
    checkpoint_database_url: str = Field(
        default="postgresql://finsight:finsight@localhost:5432/finsight",
        description="Sync DSN used by LangGraph PostgresSaver/PostgresStore.",
    )
    redis_url: str = "redis://localhost:6379/0"

    # --- Vector database (Qdrant) ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "finsight_chunks"

    # --- MCP tool server ---
    mcp_server_url: str = "http://localhost:8001/mcp"

    # --- Auth / security ---
    jwt_secret: str = "change-me-in-prod-please"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 14
    frontend_url: str = "http://localhost:5173"

    # --- Storage quota (per user) ---
    storage_quota_mb: int = 100

    # --- Google OAuth (optional; login with Google when set) ---
    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None

    # --- Email / SMTP (optional; dev returns the verification token when unset) ---
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    email_from: str = "no-reply@finsight.local"

    @property
    def emails_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_user)

    @property
    def google_oauth_enabled(self) -> bool:
        # The ID-token (GIS) flow only needs the client id to validate the token audience.
        return bool(self.google_oauth_client_id)

    # --- LLM / embeddings (Google Gemini free tier via AI Studio) ---
    llm_provider: Literal["google"] = "google"
    google_api_key: str | None = None
    llm_model: str = "gemini-2.0-flash"
    embedding_model: str = "models/gemini-embedding-2"
    embedding_dim: int = 3072

    # --- Observability ---
    langsmith_api_key: str | None = None
    langsmith_project: str = "finsight"
    langsmith_tracing: bool = False

    # --- File storage ---
    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None
    cloudinary_folder: str = "finsight"

    @property
    def is_prod(self) -> bool:
        return self.environment == "prod"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — used as a FastAPI dependency."""
    return Settings()
