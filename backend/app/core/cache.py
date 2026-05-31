"""Redis client provider.

Redis is used ONLY for caching, pub/sub task-progress streaming, rate-limiting and as the
ARQ queue backend. Conversation memory lives in Postgres via LangGraph — never here.
"""

from collections.abc import AsyncIterator

import redis.asyncio as redis

from app.core.config import Settings


def create_redis_pool(settings: Settings) -> redis.Redis:
    """Create a Redis client backed by a connection pool."""
    return redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


async def get_redis(settings: Settings) -> AsyncIterator[redis.Redis]:
    """FastAPI dependency that yields a Redis client and closes it afterwards."""
    client = create_redis_pool(settings)
    try:
        yield client
    finally:
        await client.aclose()
