# Model Card — FinSight

FinSight is a **multi-agent financial research assistant**: it answers questions about companies
from documents a user uploads (PDF / DOCX / scanned images) and from live web sources, always with
inline citations. This card documents intended use, limitations, and the responsible-AI measures
added during production hardening (Project 3).

## System overview

- **Type:** Retrieval-augmented, tool-using multi-agent system (LangGraph supervisor + Retrieval,
  Market Research, Analyst, Writer, Critic agents).
- **Base models:** Google Gemini (chat) + Gemini embeddings. FinSight does not train or fine-tune
  models; it orchestrates and grounds them.
- **Retrieval:** Hybrid (dense + keyword) search over a per-topic Qdrant collection of the user's
  own documents, with inline `[n]` citations.
- **Interfaces:** REST + SSE (chat streaming) + WebSocket (ingestion progress), React frontend.

## Intended use

- **Intended:** assisting research and analysis of financial documents and public company
  information — summarisation, figure lookup, comparison, and exploratory analysis **with citations
  the user can verify**.
- **Users:** analysts, students, and developers exploring agentic RAG. Authenticated, per-user
  workspaces.

## Out-of-scope / prohibited use

- **Not financial advice.** Outputs that read like investment guidance carry an automatic
  disclaimer; they must not be used as the sole basis for financial decisions.
- Not a system of record, not for automated trading, and not a substitute for a licensed
  professional or audited filings.

## Limitations

- **LLM limitations** — may be incomplete or wrong despite grounding; figures must be verified
  against the cited source. The Critic agent and citation requirement reduce, but do not eliminate,
  hallucination.
- **Retrieval ceiling** — answers are bounded by what was uploaded and indexed; missing or poorly
  scanned documents degrade quality. Keyword leg uses Qdrant full-text (no BM25 sparse vectors yet).
- **Free-tier rate limits** — Gemini's free tier throttles; the app retries with backoff and surfaces
  a clear message when exhausted.
- **Language/format** — tuned for English financial reports; other languages/layouts may vary.

## Responsible-AI & safety measures (Project 3)

| Risk | Mitigation | Where |
|------|-----------|-------|
| Prompt injection / jailbreak | Heuristic input guardrail refuses known patterns | [`guardrails.py`](backend/app/core/guardrails.py) |
| PII leakage into logs/model | Email/phone/card/SSN redaction before logging & prompting | same |
| Misuse as financial advice | Automatic not-financial-advice disclaimer | same |
| Ungrounded claims | Citation-required prompting + Critic grounding check | `agents/` |
| Abuse / cost runaway | Per-user rate limiting + input length cap | [`ratelimit.py`](backend/app/core/ratelimit.py) |
| Insecure deployment | Fail-fast prod config validation, non-root image | [`config.py`](backend/app/core/config.py), `Dockerfile.prod` |
| Silent failures | Structured logs + correlation ids + Prometheus metrics | `core/` |

**Safety evaluation:** `python -m evals.run_safety_eval` → injection block rate **5/5**, benign
false-positive rate **0/3**, PII redaction **2/2** (see [`evals/safety_dataset.py`](backend/evals/safety_dataset.py)).

## Data handling & privacy

- **User documents** are stored on Cloudinary (or local disk) and indexed into a **per-user,
  per-topic** Qdrant collection; retrieval is scoped so users only see their own data.
- **Conversation history** is persisted in Postgres (LangGraph checkpointer).
- **PII** in user messages is redacted before logging/tracing.
- **Secrets** are environment-only; production refuses to start with default/weak secrets.

## Monitoring in production

- Liveness `/health`, readiness `/readiness` (DB/Redis/Qdrant).
- Prometheus `/metrics`: request rate/latency/errors, LLM calls & retries, guardrail blocks,
  rate-limit hits. LangSmith traces the full agent graph.

_Last updated for AAIDC Project 3 (production hardening). See [`PRODUCTION.md`](PRODUCTION.md)._
