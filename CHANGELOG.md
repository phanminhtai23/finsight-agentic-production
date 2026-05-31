# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-05-31 — Production hardening (AAIDC Project 3)

Hardens the Module 2 multi-agent system for real-world operation. See [docs/PRODUCTION.md](docs/PRODUCTION.md).

### Added
- **Reliability:** bounded retry + exponential backoff + per-attempt timeout around all LLM and
  embedding calls (`app/core/resilience.py`); streaming retries only before the first token.
- **Safety guardrails:** prompt-injection defense, PII redaction, input-length limits, and an
  automatic not-financial-advice disclaimer on every chat path (`app/core/guardrails.py`).
- **Observability:** per-request correlation id (`X-Request-ID`), structured access logs, Prometheus
  `/metrics`, and a consistent JSON error envelope (`middleware.py`, `metrics.py`, `errors.py`).
- **Health:** `/readiness` probe checking Postgres, Redis and Qdrant connectivity.
- **Rate limiting:** Redis fixed-window, per-user, fail-open (`app/core/ratelimit.py`).
- **Secure config:** fail-fast validation refusing to boot in prod with a weak `JWT_SECRET` or
  missing keys.
- **Deployment:** hardened multi-stage non-root `Dockerfile.prod`, `docker-compose.prod.yml`, and a
  GitHub Actions CI pipeline (lint + test + coverage + frontend build).
- **Evaluation & tests:** offline adversarial safety eval (`evals/run_safety_eval.py`) plus API
  error-envelope/auth integration tests; suite grew to 69 tests.
- **Docs:** `docs/PRODUCTION.md`, `docs/MODEL_CARD.md` (responsible AI), `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `LICENSE`.

### Changed
- App version bumped to `1.0.0`; configuration extended with reliability, guardrail and rate-limit
  settings (documented in `.env.example`).

## [0.1.0] — Module 2 — Multi-agent system

Initial FinSight: LangGraph supervisor + Retrieval/Research/Analyst/Writer/Critic agents, Qdrant
hybrid RAG with citations, MCP tool server, async ingestion, React frontend, LangSmith evals.
