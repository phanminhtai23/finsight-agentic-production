"""Tests for the Redis-backed rate limiter (fixed window, fail-open)."""

import pytest
from fastapi import HTTPException

from app.core.ratelimit import enforce_rate_limit


class FakeRedis:
    """Minimal in-memory stand-in for the async Redis client used by the limiter."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.ttls: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key: str, seconds: int) -> None:
        self.ttls[key] = seconds

    async def ttl(self, key: str) -> int:
        return self.ttls.get(key, -1)


class BrokenRedis:
    async def incr(self, key: str) -> int:
        raise ConnectionError("redis unavailable")


async def test_allows_within_limit():
    redis = FakeRedis()
    for _ in range(5):
        await enforce_rate_limit(redis, "user:1", limit_per_minute=5)  # no raise


async def test_blocks_over_limit():
    redis = FakeRedis()
    for _ in range(3):
        await enforce_rate_limit(redis, "user:1", limit_per_minute=3)
    with pytest.raises(HTTPException) as exc:
        await enforce_rate_limit(redis, "user:1", limit_per_minute=3)
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


async def test_limit_is_per_identity():
    redis = FakeRedis()
    for _ in range(3):
        await enforce_rate_limit(redis, "user:1", limit_per_minute=3)
    # A different identity has its own window.
    await enforce_rate_limit(redis, "user:2", limit_per_minute=3)


async def test_fails_open_when_redis_down():
    # Limiter must not break the request path if Redis is unavailable.
    await enforce_rate_limit(BrokenRedis(), "user:1", limit_per_minute=1)
