"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.checkpointer import close_checkpointer
from app.core.config import get_settings
from app.core.db import dispose_engine, init_engine
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.metrics import render_metrics
from app.core.middleware import RequestContextMiddleware
from app.core.qdrant import close_qdrant
from app.core.queue import close_arq_pool

settings = get_settings()
configure_logging(debug=settings.debug)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks."""
    init_engine(settings)
    log.info("startup", app=settings.app_name, env=settings.environment)
    yield
    await close_arq_pool()
    await close_qdrant()
    await close_checkpointer()
    await dispose_engine()
    log.info("shutdown", app=settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Multi-Agent Financial Research Assistant",
        lifespan=lifespan,
    )

    # Correlation-id + access-log + metrics middleware (outermost, so it wraps everything).
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        payload, content_type = render_metrics()
        return Response(content=payload, media_type=content_type)

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
