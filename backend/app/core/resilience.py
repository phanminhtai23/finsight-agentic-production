"""Resilience helpers for unreliable I/O — retry with backoff, timeouts, rate-limit detection.

Production hardening (Project 3): LLM and embedding providers fail transiently (HTTP 429 rate
limits, 5xx, connection resets, slow responses). These helpers wrap such calls so a single blip
doesn't surface as a user-facing error. Retries use exponential backoff with jitter and are
bounded; every retry is logged so the behaviour is observable.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.metrics import llm_calls_total, llm_retries_total

log = get_logger(__name__)

T = TypeVar("T")

# Substrings that mark a transient provider failure worth retrying. Kept broad on purpose —
# the providers do not expose typed exceptions, so we match on the message/class name.
_TRANSIENT_MARKERS = (
    "429",
    "rate limit",
    "resource_exhausted",
    "503",
    "502",
    "504",
    "deadline",
    "timeout",
    "timed out",
    "temporarily unavailable",
    "connection reset",
    "connection aborted",
    "connection error",
    "remoteprotocolerror",
    "serviceunavailable",
)


def is_rate_limit_error(exc: BaseException) -> bool:
    """True when the exception looks like an upstream rate-limit (HTTP 429 / RESOURCE_EXHAUSTED)."""
    text = f"{type(exc).__name__} {exc}".lower()
    return "429" in text or "rate limit" in text or "resource_exhausted" in text


def is_transient_error(exc: BaseException) -> bool:
    """True when the exception is worth retrying (rate limits, 5xx, timeouts, connection drops)."""
    if isinstance(exc, asyncio.TimeoutError | TimeoutError | ConnectionError):
        return True
    text = f"{type(exc).__name__} {exc}".lower()
    return any(marker in text for marker in _TRANSIENT_MARKERS)


def _log_retry(label: str) -> Callable[[RetryCallState], None]:
    def _before_sleep(state: RetryCallState) -> None:
        exc = state.outcome.exception() if state.outcome else None
        llm_retries_total.labels(label).inc()
        log.warning(
            "retrying_transient_error",
            op=label,
            attempt=state.attempt_number,
            sleep=round(getattr(state.next_action, "sleep", 0.0), 2),
            error=str(exc) if exc else None,
        )

    return _before_sleep


async def call_with_retry(
    func: Callable[..., Awaitable[T]],
    *args: object,
    label: str,
    settings: Settings | None = None,
    timeout: float | None = None,
    **kwargs: object,
) -> T:
    """Call an async ``func`` with a per-attempt timeout and bounded exponential backoff.

    Only :func:`is_transient_error` failures are retried; anything else propagates immediately.
    The final failure is re-raised so callers can still degrade gracefully.
    """
    settings = settings or get_settings()
    eff_timeout = timeout if timeout is not None else settings.llm_timeout_seconds

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(settings.llm_max_attempts),
            wait=wait_exponential_jitter(
                initial=settings.llm_retry_initial_seconds,
                max=settings.llm_retry_max_seconds,
            ),
            retry=retry_if_exception(is_transient_error),
            before_sleep=_log_retry(label),
            reraise=True,
        ):
            with attempt:
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=eff_timeout)
                llm_calls_total.labels(label, "success").inc()
                return result
    except Exception:
        llm_calls_total.labels(label, "error").inc()
        raise

    raise AssertionError("unreachable: AsyncRetrying exhausted without raising")  # pragma: no cover
