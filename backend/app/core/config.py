"""Application configuration loaded from environment variables.

Centralizing settings here (and injecting them) keeps modules free of direct
``os.environ`` access — supporting the Dependency Inversion principle.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "change-me-in-prod-please"


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
    jwt_secret: str = DEFAULT_JWT_SECRET
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

    # --- Email via Resend HTTPS API (preferred on hosts that block SMTP ports, e.g. DigitalOcean) ---
    resend_api_key: str | None = None
    # Use a verified-domain sender in production (e.g. no-reply@finsightagent.tech).
    # "onboarding@resend.dev" works without domain verification but only delivers to the account owner.
    resend_from: str = "onboarding@resend.dev"

    @property
    def emails_enabled(self) -> bool:
        return bool(self.resend_api_key or (self.smtp_host and self.smtp_user))

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

    # --- Reliability (retry/backoff/timeout around LLM & embedding calls) ---
    llm_max_attempts: int = 4
    llm_retry_initial_seconds: float = 1.0
    llm_retry_max_seconds: float = 20.0
    llm_timeout_seconds: float = 60.0

    # --- Guardrails / safety ---
    guardrails_enabled: bool = True
    max_input_chars: int = 8000  # reject prompts longer than this (abuse / cost control)
    redact_pii_in_logs: bool = True

    # --- Rate limiting (Redis fixed-window, per authenticated user / client IP) ---
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

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

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        """Fail fast on insecure/missing config when running in production."""
        if self.environment != "prod":
            return self
        problems: list[str] = []
        if self.jwt_secret == DEFAULT_JWT_SECRET or len(self.jwt_secret) < 32:
            problems.append("JWT_SECRET must be a strong secret (>=32 chars), not the default")
        if not self.google_api_key:
            problems.append("GOOGLE_API_KEY must be set")
        if problems:
            raise ValueError("Insecure production configuration: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — used as a FastAPI dependency."""
    return Settings()
