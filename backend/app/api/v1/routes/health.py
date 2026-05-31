"""Health-check endpoints — liveness and dependency readiness.

``/health`` is a cheap liveness probe (process is up). ``/readiness`` actively checks the
backing services (Postgres, Redis, Qdrant) and returns 503 if any is unreachable, so an
orchestrator only routes traffic once dependencies are truly available.
"""

import asyncio

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.cache import create_redis_pool
from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.core.logging import get_logger
from app.core.qdrant import get_qdrant_client
from app.schemas.health import HealthResponse

router = APIRouter()
log = get_logger("health")

_APP_VERSION = "1.0.0"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe. Returns app metadata and status (no dependency checks)."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        environment=settings.environment,
        version=_APP_VERSION,
    )


async def _check_db() -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        await session.execute(text("SELECT 1"))


async def _check_redis() -> None:
    client = create_redis_pool(get_settings())
    try:
        await client.ping()
    finally:
        await client.aclose()


async def _check_qdrant() -> None:
    await get_qdrant_client(get_settings()).get_collections()


@router.get("/readiness")
async def readiness() -> JSONResponse:
    """Readiness probe — verifies Postgres, Redis and Qdrant connectivity concurrently."""
    checks = {"database": _check_db(), "redis": _check_redis(), "qdrant": _check_qdrant()}
    results = await asyncio.gather(*checks.values(), return_exceptions=True)

    statuses: dict[str, str] = {}
    healthy = True
    for name, result in zip(checks, results, strict=True):
        if isinstance(result, Exception):
            healthy = False
            statuses[name] = f"error: {type(result).__name__}"
            log.warning("readiness_dependency_down", dependency=name, error=str(result))
        else:
            statuses[name] = "ok"

    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "degraded", "dependencies": statuses},
    )
