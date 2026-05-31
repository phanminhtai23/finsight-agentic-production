"""Consistent error responses and a global exception handler.

Production hardening (Project 3): unhandled exceptions return a structured JSON envelope (never a
raw stack trace) that includes the request's correlation id, and are logged with full context so
the incident is traceable from the id the client received.
"""

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

log = get_logger("error")


def _request_id() -> str | None:
    return structlog.contextvars.get_contextvars().get("request_id")


def _envelope(code: str, message: str, *, details: Any = None) -> dict[str, Any]:
    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    rid = _request_id()
    if rid:
        body["error"]["request_id"] = rid
    if details is not None:
        body["error"]["details"] = details
    return body


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope("http_error", str(exc.detail)),
        headers=getattr(exc, "headers", None),
    )


async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_envelope("validation_error", "Request validation failed", details=exc.errors()),
    )


async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content=_envelope(
            "internal_error",
            "An unexpected error occurred. Please retry; if it persists, quote the request_id.",
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the structured error handlers to the app."""
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(Exception, _unhandled_handler)
