"""ARQ queue pool (Redis-backed) for enqueueing background jobs."""

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import Settings, get_settings

_pool: ArqRedis | None = None


def redis_settings(settings: Settings | None = None) -> RedisSettings:
    settings = settings or get_settings()
    return RedisSettings.from_dsn(settings.redis_url)


async def get_arq_pool() -> ArqRedis:
    global _pool
    if _pool is None:
        _pool = await create_pool(redis_settings())
    return _pool


async def close_arq_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
