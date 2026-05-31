"""Tests for the resilience helpers (retry/backoff/timeout + error classification)."""

import asyncio

import pytest

from app.core.config import Settings
from app.core.resilience import call_with_retry, is_rate_limit_error, is_transient_error

# Tiny delays so retry tests run fast.
FAST = Settings(
    llm_max_attempts=3,
    llm_retry_initial_seconds=0.01,
    llm_retry_max_seconds=0.02,
    llm_timeout_seconds=0.5,
)


def test_rate_limit_detection():
    assert is_rate_limit_error(RuntimeError("Error 429: RESOURCE_EXHAUSTED"))
    assert is_rate_limit_error(RuntimeError("rate limit exceeded"))
    assert not is_rate_limit_error(ValueError("bad input"))


def test_transient_detection():
    assert is_transient_error(RuntimeError("503 Service Unavailable"))
    assert is_transient_error(TimeoutError())
    assert is_transient_error(ConnectionError("connection reset by peer"))
    assert not is_transient_error(ValueError("not transient"))


async def test_retry_then_succeed():
    calls = {"n": 0}

    async def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("429 rate limit")
        return "ok"

    result = await call_with_retry(flaky, label="test", settings=FAST)
    assert result == "ok"
    assert calls["n"] == 3


async def test_non_transient_not_retried():
    calls = {"n": 0}

    async def boom() -> None:
        calls["n"] += 1
        raise ValueError("permanent")

    with pytest.raises(ValueError):
        await call_with_retry(boom, label="test", settings=FAST)
    assert calls["n"] == 1  # never retried


async def test_exhausts_and_reraises():
    async def always_429() -> None:
        raise RuntimeError("429 RESOURCE_EXHAUSTED")

    with pytest.raises(RuntimeError):
        await call_with_retry(always_429, label="test", settings=FAST)


async def test_timeout_is_transient_and_retried():
    calls = {"n": 0}

    async def slow_then_fast() -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            await asyncio.sleep(1.0)  # exceeds the 0.5s timeout → TimeoutError (transient)
        return "done"

    result = await call_with_retry(slow_then_fast, label="test", settings=FAST)
    assert result == "done"
    assert calls["n"] == 2
