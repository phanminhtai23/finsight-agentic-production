# FinSight — Backend

FastAPI backend for **FinSight**, a multi-agent financial research assistant.
It hosts the REST + WebSocket API, the LangGraph multi-agent graph, the RAG layer
(ingestion → chunking → indexing → retrieval), the MCP tool server, and the async task
workers.

> This is the `backend/` package of the FinSight monorepo. For the product overview and the
> full system design, see the root [README](../README.md) and [ARCHITECTURE](../ARCHITECTURE.md).

## Tech

- **Python 3.11+** (developed on 3.12)
- FastAPI · LangGraph · LangChain · **Google Gemini** (free tier)
- **Qdrant** (vectors) · PostgreSQL (relational + LangGraph checkpointer) · Redis · ARQ
- SQLAlchemy 2 (async) · Alembic · Cloudinary
- Tooling: **ruff**, **pytest**

## Layout

```
app/
├── api/            FastAPI routers (REST + WebSocket) — thin controllers
│   └── v1/routes/  health, conversations, documents, tasks, ws
├── core/           config, logging, db (async engine/session), cache (redis)
├── schemas/        Pydantic request/response DTOs
├── services/       business logic (ingestion, retrieval/QA, conversation, task)
├── repositories/   data access behind Protocol interfaces  ← SOLID DIP
├── agents/         LangGraph graph, agent nodes, supervisor, shared state
├── tools/          tool implementations + MCP client adapter
├── rag/            ingestion · chunking · indexing · retrieval
├── skills/         reusable skill packages
├── workers/        ARQ background workers (ingestion, research)
└── models/         SQLAlchemy ORM (documents, conversations, messages, tasks)
mcp_server/         MCP server exposing tools (rag_search, web_search, fetch_url, fin_calc)
evals/              LangSmith datasets + evaluation scripts
tests/              pytest (unit + integration)
alembic/            database migrations
```

## Configuration

All settings come from environment variables (see [`app/core/config.py`](app/core/config.py)).
Copy the example env from the repo root and fill in keys:

```bash
cp ../.env.example ../.env
```

Required keys:

| Variable | Purpose | Where to get it |
|----------|---------|-----------------|
| `GOOGLE_API_KEY` | Gemini LLM + embeddings (free) | https://aistudio.google.com/apikey |
| `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` | Raw file storage | https://cloudinary.com (free tier) |
| `DATABASE_URL` / `CHECKPOINT_DATABASE_URL` | Postgres (async + sync DSNs) | provided by docker-compose |
| `QDRANT_URL` / `QDRANT_API_KEY` / `QDRANT_COLLECTION` | Vector store | provided by docker-compose |
| `REDIS_URL` | Cache / pub-sub / ARQ queue | provided by docker-compose |
| `LANGSMITH_API_KEY` *(optional)* | Tracing + eval | https://smith.langchain.com |

## Running

### With Docker (recommended — full stack)
From the repo root:
```bash
docker compose up --build
```
API at http://localhost:8000 (interactive docs at `/docs`).

### Local dev (Python 3.12)
```bash
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate          # PowerShell:  .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Postgres + Qdrant + Redis still needed — start just those:
docker compose up -d postgres qdrant redis

# apply migrations, then run the API
alembic upgrade head
uvicorn app.main:app --reload
```

## Database migrations (Alembic)

```bash
alembic revision --autogenerate -m "message"   # create a migration
alembic upgrade head                            # apply
alembic downgrade -1                            # roll back one
```

## Background worker (ARQ)

Long-running jobs (document ingestion, deep research) run outside the request cycle so the
user can keep chatting. Start a worker with:
```bash
arq app.workers.settings.WorkerSettings
```

## Quality

```bash
ruff check .          # lint
ruff format .         # format
pytest                # tests
pytest --cov=app      # tests + coverage
```

## API (v1, under `/api/v1`)

| Method | Path | Description |
|--------|------|-------------|
| GET  | `/health` | Liveness/readiness probe |
| POST | `/conversations` | Create a conversation |
| POST | `/conversations/{id}/messages` | Send a chat message |
| POST | `/documents` | Upload a document → async ingestion |
| GET  | `/documents/{id}` | Ingestion status |
| POST | `/conversations/{id}/tasks` | Launch a long-running task |
| GET  | `/tasks/{id}` | Task status / result |
| WS   | `/ws/conversations/{id}` | Stream tokens & task progress |

*(Endpoints are delivered incrementally per milestone — see the roadmap in the root README.)*
