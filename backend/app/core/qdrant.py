"""Qdrant async client (process-wide singleton)."""

from qdrant_client import AsyncQdrantClient

from app.core.config import Settings, get_settings

_client: AsyncQdrantClient | None = None


def get_qdrant_client(settings: Settings | None = None) -> AsyncQdrantClient:
    global _client
    if _client is None:
        settings = settings or get_settings()
        _client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return _client


async def close_qdrant() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
