# SupportForge

A RAG-powered Telegram support bot. Users ask questions or upload documents (PDF/Markdown/text) via Telegram; the bot answers using a retrieval-augmented generation pipeline over the uploaded knowledge base, running entirely on local models (Ollama). Every answer is versioned, traceable, and automatically scored for faithfulness and hallucination, with background workers, synthetic incident simulation, and a monitoring stack layered on top.

## Architecture

```
Telegram ──▶ FastAPI app (app/main.py) ──▶ LangGraph workflow (retrieve ─▶ generate)
                 │                              │                 │
                 │                       Qdrant (vectors)   Ollama (chat + embeddings)
                 │
                 ├─▶ Postgres (conversations, messages, documents, feedback,
                 │              evaluations, prompt_versions)
                 │
                 ├─▶ Celery + Redis (background: ingestion, evaluation, nightly
                 │                    incident simulation via Celery beat)
                 │
                 ├─▶ Langfuse (LLM call tracing, optional — no-ops if unset)
                 │
                 └─▶ Prometheus + Grafana (HTTP latency, token usage; evaluation
                                            score trends read from Postgres directly)
```

The FastAPI process and the Telegram bot's polling loop run in the same process (started/stopped together in `app/main.py`'s lifespan handler). Postgres and Ollama are expected to run natively on the host, not in containers; everything else (Qdrant, Redis, Prometheus, Grafana, and optionally the backend/Celery themselves) can run via Docker Compose.

## Features

- **Chat**: LangGraph `retrieve → generate` workflow. Retrieval does a top-5 similarity search in Qdrant (768-dim, cosine, `nomic-embed-text` embeddings); generation calls Ollama with the active system prompt plus retrieved context.
- **Knowledge ingestion**: Upload a PDF/Markdown/text file via Telegram or `POST /knowledge/upload`. Files are chunked (800 chars, 100 overlap), embedded, and indexed into Qdrant asynchronously via Celery.
- **Prompt versioning**: System prompts are stored in a `prompt_versions` table, not hardcoded. `get_active_prompt` seeds version 1 from `app/llm/prompts/support.md` on first use; `scripts/update_prompt.py` promotes a new version live without redeploying (the graph reads the active prompt fresh from the DB per request).
- **Tracing**: Every generation call is wrapped in a Langfuse observation (`app/monitoring/tracing.py`).
- **Evaluation**: Every message can be scored for `faithfulness` and `hallucination` (DeepEval, judged by a local Ollama model) and `context_precision`/`context_recall` (Ragas, via Ollama's OpenAI-compatible endpoint). Runs automatically on 👎 feedback, or on-demand via `/incident`.
- **Background workers**: Document ingestion and evaluation both run as Celery tasks (Redis broker/backend) so Telegram replies aren't blocked on slow work.
- **Incident simulation**: `/incident <name>` (or a nightly Celery beat job at 03:00) generates realistic customer messages for 4 personas (angry, confused, technical, scammer) against a canned incident (`payment_gateway_down`, `account_locked`, `shipping_delay`), runs them through the real chat pipeline, evaluates every response, and reports aggregate scores plus the worst-scoring answer — useful for catching regressions or knowledge-base gaps before real users do.
- **Monitoring**: `/metrics` exposes HTTP latency and chat token usage for Prometheus; a provisioned Grafana dashboard visualizes them. Evaluation score trends are queried directly from Postgres in Grafana (not Prometheus), since evaluation only ever runs inside the Celery worker process, which has its own separate metrics registry.

## Project structure

```
app/
  api/            HTTP routes: health, chat, knowledge
  database/       SQLAlchemy async models + session (models.py, session.py)
  evaluation/     DeepEval + Ragas scoring, evaluator orchestration
  graph/          LangGraph state + retrieve/generate workflow
  llm/            Ollama client, DB-backed prompt versioning (llm/prompts/)
  monitoring/     Langfuse tracing, Prometheus metrics + /metrics route
  rag/            loader, chunker, embedder, indexer, retriever
  schemas/        Pydantic request/response models
  services/       chat_service, knowledge_service (business logic used by both API and Telegram)
  simulator/      personas, message generation, canned incidents, Celery beat scheduler
  telegram/       bot wiring, commands (/start /help /report /incident), message handlers
  workers/        Celery app + task wrappers around ingestion/evaluation
  config.py       pydantic-settings Settings (env vars)
  main.py         FastAPI app, lifespan (DB + bot startup), middleware, routers
scripts/
  update_prompt.py   promote support.md content to a new active prompt version
monitoring/
  prometheus/     prometheus.yml scrape config
  grafana/        provisioned datasource + dashboard JSON
tests/            pytest suite (health, chat, knowledge upload)
docker-compose.yml  qdrant, redis, backend, celery-worker, celery-beat, prometheus, grafana
Dockerfile
```

## Setup

### Prerequisites (run natively on the host, not in Docker)

- **Postgres** — a running instance with a database created for this project.
- **Ollama** — with the chat and embedding models pulled:
  ```bash
  ollama pull qwen2.5:7b
  ollama pull nomic-embed-text
  ```
- **Python 3.12** and [uv](https://docs.astral.sh/uv/).

### Configure environment

Copy `.env.example` to `.env` and fill in values:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Full Postgres connection string (used when running natively) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_PORT` / `POSTGRES_DB` | Same credentials, decomposed — used by docker-compose to rebuild `DATABASE_URL` with `host.docker.internal` for containerized backend/Celery. Password must be URL-encoded (e.g. `@` → `%40`). |
| `QDRANT_URL` | Qdrant endpoint (`http://localhost:6333` by default, runs via docker-compose) |
| `OLLAMA_BASE_URL` | Ollama endpoint (native on host) |
| `OLLAMA_CHAT_MODEL` / `OLLAMA_EMBED_MODEL` | Model names, default `qwen2.5:7b` / `nomic-embed-text` |
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather (required) |
| `TELEGRAM_CHAT_ID` | Restricts `/report` and `/incident` to this chat ID if set |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_BASE_URL` | Optional — tracing no-ops if unset |
| `REDIS_URL` | Redis endpoint, Celery broker/backend (runs via docker-compose) |

### Install dependencies

```bash
uv sync
```

## Running

Start the supporting services (Qdrant, Redis, and optionally Prometheus/Grafana):

```bash
docker compose up -d qdrant redis prometheus grafana
```

Run the backend (FastAPI + Telegram bot) and Celery worker natively:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
uv run celery -A app.workers.celery_app worker --loglevel=info
```

For scheduled nightly incident simulations, also run Celery beat:

```bash
uv run celery -A app.workers.celery_app beat --loglevel=info
```

Alternatively, `docker compose up -d` can build and run `backend`/`celery-worker`/`celery-beat` as containers too — but they need Postgres and Ollama reachable from inside Docker (`host.docker.internal`), which requires Postgres to accept connections beyond `127.0.0.1`. Running them natively avoids that.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/` , `/health` | Liveness check |
| `POST` | `/chat` | `{chat_id, message}` → runs the RAG workflow, returns the answer |
| `POST` | `/knowledge/upload` | Multipart file upload (`.pdf`/`.md`/`.markdown`/`.txt`), enqueues async ingestion |
| `GET` | `/metrics` | Prometheus exposition format |

## Telegram bot

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/help` | Usage help |
| `/report` | Owner-only. Reports the 5 worst-scoring evaluated messages (by faithfulness) |
| `/incident <name>` | Owner-only. Runs a simulated incident (`payment_gateway_down`, `account_locked`, `shipping_delay`) across all personas, evaluates every response, and reports aggregate scores + the worst answer |

Plain text messages are answered via the RAG pipeline with an inline 👍/👎 feedback keyboard; a 👎 automatically triggers evaluation of that message. Document uploads (PDF/Markdown/text) are ingested into the knowledge base in the background.

## Evaluation

Every evaluated message gets four scores, written to the `evaluations` table:

- `faithfulness` (DeepEval) — higher is better; how well the answer is grounded in retrieved context.
- `hallucination` (DeepEval) — higher is **worse**; degree to which the answer contradicts or goes beyond retrieved context.
- `context_precision` (Ragas) — higher is better; how relevant the retrieved chunks were.
- `context_recall` (Ragas) — higher is better; how much of what's needed to answer was actually retrieved.

Low `context_precision`/`context_recall` usually signals a knowledge-base gap (nothing relevant was ingested for that topic) rather than a pipeline bug.

## Monitoring

- **Prometheus** (`:9090`) scrapes `/metrics` from the backend for HTTP request latency and chat token usage.
- **Grafana** (`:3000`, default `admin`/`admin`) has a provisioned dashboard (`supportforge`) with panels for HTTP latency (p95), request rate by path, and chat token usage, all sourced from Prometheus.
- **Langfuse Cloud** traces every generation call (prompt, response, latency) when credentials are configured.

## Testing

```bash
uv run pytest
```

Covers `/health`, `/`, `/chat`, and `/knowledge/upload`. RAG internals, evaluation, the simulator, and Telegram handlers are exercised through live/manual testing rather than unit tests.
