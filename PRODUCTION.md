# Production Hardening (AAIDC Project 3)

FinSight was built as a multi-agent RAG system in Project 2. **Project 3 hardens it for real-world
operation** — reliability, safety, observability, and deployment — without changing what it does.
This document is the map of *what* was added, *where* it lives, and *how to verify* it.

> TL;DR: retries + timeouts around every model call · a safety guardrail layer (injection / PII /
> disclaimer) · request-correlated structured logs + Prometheus metrics + global error envelope ·
> readiness probes · per-user rate limiting · fail-fast prod config · CI (lint+test+build) ·
> hardened Docker image & compose · an offline adversarial safety eval.

---

## 1. Reliability — surviving a flaky model provider

The Gemini free tier returns transient `429 / RESOURCE_EXHAUSTED`, 5xx and timeouts. Every model
and embedding call now runs through a bounded **retry + exponential-backoff-with-jitter + timeout**
wrapper.

| Where | What |
|-------|------|
| [`app/core/resilience.py`](backend/app/core/resilience.py) | `call_with_retry()` — per-attempt timeout, retries only *transient* errors, re-raises otherwise; `is_transient_error()` / `is_rate_limit_error()` classifiers |
| [`app/core/llm.py`](backend/app/core/llm.py) | embeddings, `generate()` and `stream_chat()` wrapped. Streaming retries **only before the first token** so it never duplicates mid-stream output |
| Config | `LLM_MAX_ATTEMPTS`, `LLM_RETRY_INITIAL_SECONDS`, `LLM_RETRY_MAX_SECONDS`, `LLM_TIMEOUT_SECONDS` |

**Verify:** `pytest tests/test_resilience.py` (retry-then-succeed, non-transient not retried, timeout treated as transient, exhaustion re-raises).

## 2. Safety guardrails — input & output

A fast, dependency-free safety layer runs **before** the prompt reaches the LLM and **after** the
answer is produced. ([`app/core/guardrails.py`](backend/app/core/guardrails.py))

- **Input validation** — empty / over-length rejection (`MAX_INPUT_CHARS`, cost & abuse control).
- **Prompt-injection defense** — heuristics for "ignore previous instructions / reveal your system
  prompt / act as DAN / developer mode …". Flagged input is **refused, not forwarded**.
- **PII redaction** — emails, phone, credit-card and SSN-like numbers masked before they reach
  logs, traces or the model.
- **Not-financial-advice disclaimer** — appended to investment-style answers.

Wired into both chat paths: [`streaming_chat_service.py`](backend/app/services/streaming_chat_service.py)
and [`qa_service.py`](backend/app/services/qa_service.py).

**Verify:** `pytest tests/test_guardrails.py tests/test_safety_eval.py` and
`python -m evals.run_safety_eval` → injection block rate **5/5**, benign false-positives **0/3**,
PII redaction **2/2**.

## 3. Observability — logs, metrics, errors

| Concern | Where |
|---------|-------|
| **Correlation id** per request, bound to all logs, echoed as `X-Request-ID` | [`app/core/middleware.py`](backend/app/core/middleware.py) |
| **Structured access logs** (method, path, status, duration) | same middleware, JSON in prod via [`logging.py`](backend/app/core/logging.py) |
| **Prometheus `/metrics`** — request count/latency, LLM calls/retries, guardrail blocks, rate-limit hits | [`app/core/metrics.py`](backend/app/core/metrics.py) |
| **Global error envelope** — `{"error": {code, message, request_id}}`, never a raw stack trace | [`app/core/errors.py`](backend/app/core/errors.py) |
| **Tracing** — LangSmith across the agent graph (`LANGSMITH_TRACING=true`) | existing |

**Verify:** `pytest tests/test_api_errors.py tests/test_health.py` then `curl localhost:8000/metrics`.

## 4. Health & readiness

- `GET /api/v1/health` — liveness (process up).
- `GET /api/v1/readiness` — actively checks **Postgres, Redis, Qdrant** concurrently; returns
  `503 degraded` if any dependency is down so an orchestrator won't route traffic prematurely.

[`app/api/v1/routes/health.py`](backend/app/api/v1/routes/health.py) · **Verify:** `pytest tests/test_health.py`.

## 5. Rate limiting

Redis fixed-window limiter, keyed per authenticated user, on the expensive chat endpoint. **Fails
open** if Redis is unavailable (availability over enforcement). `RATE_LIMIT_PER_MINUTE`,
`RATE_LIMIT_ENABLED`. ([`app/core/ratelimit.py`](backend/app/core/ratelimit.py))

**Verify:** `pytest tests/test_ratelimit.py`.

## 6. Secure-by-default config & deployment

- **Fail-fast prod validation** — the app refuses to boot in `ENVIRONMENT=prod` with a default/weak
  `JWT_SECRET` or a missing `GOOGLE_API_KEY`. ([`config.py`](backend/app/core/config.py), `pytest tests/test_config.py`)
- **Hardened image** — [`backend/Dockerfile.prod`](backend/Dockerfile.prod): multi-stage, non-root
  user, container `HEALTHCHECK`, multi-worker uvicorn.
- **Production orchestration** — [`docker-compose.prod.yml`](docker-compose.prod.yml): built images
  (no source mounts), `restart: unless-stopped`, dependency healthchecks.
- **CI** — [`.github/workflows/ci.yml`](.github/workflows/ci.yml): ruff lint + format check + pytest
  (with coverage) on the backend, and tsc + vite build on the frontend, on every push/PR.

---

## Evaluation summary

| Dimension | Tooling | Result |
|-----------|---------|--------|
| Answer quality (RAG vs no-RAG baseline) | `evals/run_eval.py` (LangSmith) | recall, citation coverage, LLM-judge groundedness |
| **Safety / guardrails** | `evals/run_safety_eval.py` (offline) | injection block **5/5**, benign FP **0/3**, PII **2/2** |
| Regression gates | `pytest` (69 tests) | reliability, guardrails, rate-limit, health, errors, config |

## Configuration reference (new in Project 3)

```env
# Reliability
LLM_MAX_ATTEMPTS=4
LLM_RETRY_INITIAL_SECONDS=1.0
LLM_RETRY_MAX_SECONDS=20.0
LLM_TIMEOUT_SECONDS=60.0
# Guardrails
GUARDRAILS_ENABLED=true
MAX_INPUT_CHARS=8000
REDACT_PII_IN_LOGS=true
# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

See [`MODEL_CARD.md`](MODEL_CARD.md) for intended use, limitations and responsible-AI considerations.
