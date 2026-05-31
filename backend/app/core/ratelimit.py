"""Redis-backed fixed-window rate limiter.

Production hardening (Project 3): protects expensive endpoints (chat, ask, upload) from abuse
and runaway cost. Uses an atomic ``INCR`` on a per-identity, per-minute key with a TTL — simple,
fast, and shared across all API replicas via Redis. Fails open: if Redis is unavailable the
request is allowed (availability over enforcement), and the event is logged.
"""

import redis.asyncio as redis
from fastapi import HTTPException, status

from app.core.logging import get_logger
from app.core.metrics import rate_limited_total

log = get_logger("ratelimit")

_WINDOW_SECONDS = 60


async def enforce_rate_limit(client: redis.Redis, identity: str, limit_per_minute: int) -> None:
    """Increment the caller's window counter; raise HTTP 429 when the limit is exceeded."""
    key = f"ratelimit:{identity}"
    try:
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, _WINDOW_SECONDS)
        ttl = await client.ttl(key)
    except Exception as exc:  # noqa: BLE001 - fail open if Redis is down
        log.warning("rate_limit_backend_unavailable", error=str(exc))
        return

    if count > limit_per_minute:
        rate_limited_total.inc()
        retry_after = ttl if ttl and ttl > 0 else _WINDOW_SECONDS
        log.warning("rate_limited", identity=identity, count=count, limit=limit_per_minute)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down and try again shortly.",
            headers={"Retry-After": str(retry_after)},
        )
