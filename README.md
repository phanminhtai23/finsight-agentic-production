<p align="center">
  <img src="frontend/public/logo.svg" width="88" alt="FinSight logo" />
</p>

<h1 align="center">FinSight</h1>

<p align="center">
  <b>Multi-Agent Financial Research Assistant</b><br/>
  Grounded answers with citations — from your documents and the live web.
</p>

<p align="center">
  <img alt="status" src="https://img.shields.io/badge/tests-passing-brightgreen" />
  <img alt="python" src="https://img.shields.io/badge/python-3.12-blue" />
  <img alt="license" src="https://img.shields.io/badge/license-MIT-black" />
</p>

---

> Submission for **Ready Tensor — Agentic AI Developer Certification (AAIDC), Module 2: Build Your Multi-Agent System**.

FinSight is a production-style, multi-agent system that answers financial questions about **any company** — either from documents you upload (PDF, Word, scanned images) or from live web/financial sources — and **always answers with inline citations** back to the exact source page.

It is built around a LangGraph supervisor orchestrating a team of specialized agents, a retrieval-augmented-generation (RAG) layer with advanced chunking and hybrid search, tools exposed through a dedicated **MCP server**, and an async task engine that lets you keep chatting while long jobs (document ingestion, deep research) run in the background.

---

## 🧪 Quick demo (for reviewers)

A ready-made report lives at [`samples/sample_financial_report.docx`](samples/sample_financial_report.docx) — *Nimbus Cloud Inc. FY2024*, with quarterly results and a revenue-by-segment breakdown (good for trends, comparisons and pie charts).

**1. Start everything**
```bash
cp .env.example .env          # then set GOOGLE_API_KEY (free: https://aistudio.google.com/apikey)
docker compose up -d --build  # postgres, qdrant, redis, mcp, api, worker
docker compose exec api alembic upgrade head
cd frontend && npm install && npm run dev   # → http://localhost:5173
```

**2. Sign up** at http://localhost:5173 → *Get started*.
> Email verification: when SMTP is not configured, the app runs in dev mode and verifies you automatically (no inbox needed).

**3. Add the sample data** → in the app click **Manage data (topics)** → create a topic `Nimbus` → **Upload file** → choose `samples/sample_financial_report.docx` → wait for status **ready**.

**4. Chat** → **+ New** conversation, pin the **Nimbus** topic, then try:

| Ask | What to expect |
|-----|----------------|
| `What was Q4 2024 revenue and net income?` | Grounded answer **$1,180M / $262M** with a clickable `[1]` citation |
| `Plot quarterly revenue for 2024 as a chart` | A line/bar **chart** (820 → 910 → 1,015 → 1,180) |
| `Show revenue breakdown by segment as a pie chart` | A **pie** (Cloud 50% · Data 28% · AI 22%) |
| `Is Nimbus a good investment? Analyze with a chart.` | Analyst-style take + risks + a chart |

**5. Also try:** dark mode, the **Thinking** toggle (streams the agent's reasoning), collapsing the sidebar, your profile (Free tier). Charts and citations persist on reload.

> Gemini's free tier is rate-limited; if a reply is throttled the UI says so — wait ~1 minute and retry.

---

## ✨ Key Features

- **Multi-agent orchestration (LangGraph supervisor)** — six focused agents (Supervisor, Retrieval, Market Research, Analyst, Writer, Critic) coordinating to solve a task.
- **RAG over your own documents** — upload PDF / DOCX / scanned images; FinSight parses, OCRs, chunks and indexes them into a **Qdrant** vector store.
- **Advanced chunking** — layout-aware + semantic + parent–child + Anthropic-style *contextual retrieval*, with table-aware handling for financial statements.
- **Hybrid retrieval + reranking** — vector search fused with full-text (BM25-like) search, then cross-encoder reranking.
- **Citations everywhere** — every claim is traceable to a document, page and region (deep-link to the file on Cloudinary).
- **Live financial research** — web search + financial APIs via MCP tools for companies not in your documents.
- **Async & concurrent** — long-running ingestion / research runs in background workers; you can keep chatting in the same conversation. Progress streams live over WebSocket.
- **Durable memory** — conversation state and long-term user memory persisted in **Postgres** via LangGraph's built-in checkpointer/store.
- **Observability** — full tracing and evaluation with LangSmith.

## 🏗️ Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design, agent roles, communication flows, RAG pipeline and data model.

```mermaid
flowchart TD
    U["🖥️ React UI / API client"] -->|"REST + WebSocket"| API["⚡ FastAPI<br/>(RESTful · SOLID)"]

    subgraph AGENTS["🤖 LangGraph multi-agent graph"]
        direction TB
        SUP(["🧭 Supervisor<br/>triage &amp; route"])
        RET["📚 Retrieval<br/>(RAG)"]
        MR["🌐 Market Research"]
        AN["📊 Analyst"]
        WR["✍️ Writer<br/>+ citations"]
        CR["🔎 Critic<br/>grounding check"]
        SUP --> RET --> AN --> WR --> CR
        SUP --> MR --> AN
        CR -.->|"revise ≤2"| AN
    end
    API --> SUP

    subgraph DATA["🗄️ Datastores"]
        QD[("Qdrant<br/>vectors")]
        PG[("Postgres<br/>relational + checkpointer")]
        RD[("Redis<br/>cache · pubsub · queue")]
    end

    subgraph EXT["🧰 Tools &amp; services"]
        MCP["🔌 MCP server<br/>web_search · fetch_url<br/>company_financials · calculator"]
        CL["☁️ Cloudinary<br/>raw files"]
        LS["📈 LangSmith<br/>tracing &amp; eval"]
    end

    RET --> QD
    MR -->|"MCP client"| MCP
    API --> PG
    API --> RD
    API --> WK["⏳ ARQ worker<br/>async ingestion"]
    WK --> CL
    WK --> QD
    API -.->|"trace"| LS
```

## 🧰 Tech Stack

| Layer | Tech |
|-------|------|
| Orchestration | LangGraph, LangChain |
| LLM / Embeddings | Google Gemini — chat (e.g. `gemini-3.1-flash-lite-preview`) + `gemini-embedding-2` (3072-d) |
| Vector store | Qdrant |
| Relational store | PostgreSQL |
| Tools protocol | Model Context Protocol (MCP) server |
| Cache / bus / queue | Redis, ARQ |
| Conversation memory | Postgres (LangGraph `PostgresSaver` + `PostgresStore`) |
| File storage | Cloudinary |
| API | FastAPI (RESTful) |
| Frontend | React + Vite + TypeScript |
| Observability | LangSmith |
| Quality | ruff, pytest |

## 🚀 Getting Started

### Prerequisites
- **Docker & Docker Compose** (recommended) — runs the whole stack.
- *(optional, local dev only)* Python 3.11+, Node 20+

### 1. Get the API keys

| Variable | Required? | Where to get it |
|----------|-----------|-----------------|
| `GOOGLE_API_KEY` | ✅ **Required** | [Google AI Studio](https://aistudio.google.com/apikey) → *Create API key* (free). Used for the chat LLM + embeddings. |
| `CLOUDINARY_CLOUD_NAME` · `CLOUDINARY_API_KEY` · `CLOUDINARY_API_SECRET` | Optional | [cloudinary.com](https://cloudinary.com/users/register_free) → register free → **Dashboard → Product Environment Credentials**. |
| `LANGSMITH_API_KEY` | Optional | [smith.langchain.com](https://smith.langchain.com) → *Settings → API Keys* (enables tracing + eval; set `LANGSMITH_TRACING=true`). |

> Without Cloudinary, uploaded files fall back to local disk (`uploads/`). Without LangSmith, tracing is simply disabled. **Only `GOOGLE_API_KEY` is needed to run.**

### 2. Configure environment
```bash
cp .env.example .env
# open .env and paste your GOOGLE_API_KEY (minimum); optionally Cloudinary + LangSmith.
```

The **default database account** is defined in `.env` and created automatically when Postgres first starts — change these to set your own credentials:
```env
POSTGRES_USER=finsight
POSTGRES_PASSWORD=finsight
POSTGRES_DB=finsight
```

### 3. Run with Docker
```bash
docker compose up -d --build                  # build + start all services in the background
docker compose exec api alembic upgrade head  # first run only: create the DB schema
```
Services & URLs:
- **API** — http://localhost:8000  (Swagger docs at `/docs`)
- **Qdrant dashboard** — http://localhost:6333/dashboard

### 4. Run the frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev          # → http://localhost:5173 (proxies /api to the backend)
```

### Managing the project (Docker Compose)
```bash
docker compose ps                 # show services + status
docker compose logs -f api        # follow logs of one service (api | worker | mcp | postgres | qdrant | redis)
docker compose stop               # stop all services       (data is kept)
docker compose start              # start them again
docker compose restart api        # restart a single service (e.g. after editing code)
docker compose up -d --build      # rebuild + restart after changing dependencies
docker compose down               # remove containers + network (KEEPS data volumes)
docker compose down -v            # remove EVERYTHING incl. volumes (wipes Postgres + Qdrant data)
```

### 3. Local backend dev (without Docker)
```bash
cd backend
pip install -e ".[dev]"      # or: uv pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## 🔌 API Overview (RESTful)

| Method | Path | Description |
|--------|------|-------------|
| GET  | `/api/v1/health` | Liveness/readiness probe |
| POST | `/api/v1/conversations` | Create a conversation |
| POST | `/api/v1/conversations/{id}/messages` | Send a message (chat) |
| POST | `/api/v1/documents` | Upload a document → triggers async ingestion |
| GET  | `/api/v1/documents/{id}` | Ingestion status |
| POST | `/api/v1/conversations/{id}/tasks` | Launch a long-running task |
| GET  | `/api/v1/tasks/{id}` | Task status / result |
| WS   | `/api/v1/ws/conversations/{id}` | Stream tokens & task progress |

## 🧪 Quality

```bash
cd backend
ruff check .          # lint
ruff format .         # format
pytest                # tests
```

## 📁 Project Structure

```
backend/app/
├── api/            FastAPI routers (REST + WebSocket) — thin controllers
├── core/           config, logging, cache, DI
├── schemas/        Pydantic request/response DTOs
├── services/       business logic
├── repositories/   data access (Protocol + impl)  ← SOLID DIP
├── agents/         LangGraph graph, nodes, supervisor, state
├── tools/          tool implementations + MCP client adapter
├── rag/            ingestion · chunking · indexing · retrieval
├── skills/         reusable skill packages
├── workers/        ARQ background workers
└── models/         SQLAlchemy ORM
backend/mcp_server/  MCP server exposing tools
frontend/            React + Vite + TS
```

## 🗺️ Roadmap

- [x] M0 — Scaffold, config, Docker, lint/test baseline
- [x] M1 — RAG core (ingestion + Qdrant + hybrid retriever + cited QA)
- [x] M2 — Multi-agent graph (supervisor + agents) on LangGraph + Postgres checkpointer
- [x] M3 — Tools via MCP server (web_search, company_financials, fetch_url, financial_calculator)
- [x] M4 — Async tasks (ARQ + Redis pub/sub + WebSocket)  *(ingestion path)*
- [x] M5 — React frontend (landing, auth, topics + upload, chat streaming, thinking, dark mode)
- [x] M6 — Skills (`/skills`) + LangSmith evals (RAG vs baseline) + publication

## 📄 License

MIT
