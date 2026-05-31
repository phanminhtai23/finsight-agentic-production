"""HTTP middleware — per-request correlation ID, structured access logs, and metrics.

Production hardening (Project 3). Every request gets a unique ``request_id`` that is bound to the
structlog context (so all logs emitted while handling the request carry it) and returned in the
``X-Request-ID`` response header for client-side correlation. Latency and status are recorded to
Prometheus and logged as a single structured access line.
"""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.core.metrics import http_request_duration_seconds, http_requests_total

log = get_logger("http")

REQUEST_ID_HEADER = "X-Request-ID"


def _route_label(request: Request) -> str:
    """Use the matched route template (not the raw path) to keep metric cardinality bounded."""
    route = request.scope.get("route")
    return getattr(route, "path", None) or request.url.path


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            self._record(request, 500, time.perf_counter() - start, request_id)
            structlog.contextvars.clear_contextvars()
            raise

        response.headers[REQUEST_ID_HEADER] = request_id
        self._record(request, status, time.perf_counter() - start, request_id)
        structlog.contextvars.clear_contextvars()
        return response

    @staticmethod
    def _record(request: Request, status: int, elapsed: float, request_id: str) -> None:
        label = _route_label(request)
        # /metrics scrapes shouldn't pollute their own series.
        if label != "/metrics":
            http_requests_total.labels(request.method, label, str(status)).inc()
            http_request_duration_seconds.labels(request.method, label).observe(elapsed)
        log.info(
            "request",
            status=status,
            duration_ms=round(elapsed * 1000, 1),
            request_id=request_id,
        )
