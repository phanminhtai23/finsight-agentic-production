"""ARQ worker configuration.

Run with:  arq app.workers.settings.WorkerSettings
"""

from typing import Any

from app.core.config import get_settings
from app.core.db import init_engine
from app.core.queue import redis_settings
from app.workers.tasks import ingest_document


async def startup(ctx: dict[str, Any]) -> None:
    init_engine(get_settings())


class WorkerSettings:
    functions = [ingest_document]
    on_startup = startup
    redis_settings = redis_settings()
    max_jobs = 5
    job_timeout = 600  # seconds — long enough for large-document ingestion
