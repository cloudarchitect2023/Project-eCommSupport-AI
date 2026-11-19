# Project - eCommSupport-AI

An eCommerce support assistant built to satisfy the five milestones in [Readme6.md](./Readme6.md). It separates the Streamlit frontend, FastAPI backend, MySQL-compatible data layer/MCP server, Pinecone policy retrieval, conversation memory, and evaluations.

## Architecture

See [architecture.md](./architecture.md) for the architecture diagram, request flows, trust boundaries, and a milestone-by-milestone component map.

## Project layout by responsibility and milestone

| Milestone | Frontend | Backend / orchestration | Database / retrieval | Other deliverables |
|---|---|---|---|---|
| 1. Structured data + MCP | `frontend/app.py` provides product and order chat | `backend/mcp_server.py`, `backend/mcp_client.py`, `backend/database.py` expose only fixed parameterized operations | `database/schema.sql`; SQLAlchemy models support local SQLite and MySQL | `scripts/init_db.py`; `tests/test_database.py` |
| 2. Advanced RAG | Retrieval-mode selector in `frontend/app.py` | `backend/rag.py` implements Simple, HyDE, and Multi-Query retrieval | Pinecone vector index; curated source documents in `data/policies.jsonl` | `scripts/ingest_policies.py`, `scripts/benchmark_retrieval.py`; retrieval tests |
| 3. Agent + persistent memory | Chat transcript and source display in `frontend/app.py` | `backend/agent.py` performs tool calling, routing, and citations | `backend/memory.py` stores bounded session memory in Upstash Redis or a local demo store | `backend/api.py` serves chat requests |
| 4. Guardrails + context/cost | UI constrains the customer support workflow | `backend/guardrails.py` validates input/redacts PII; `backend/agent.py` summarizes older turns and routes simple/complex work | Redis stores rolling summary plus a bounded number of recent turns | Prompt boundaries and explicit production-authentication notes |
| 5. Evaluations | UI displays tool/model/latency metadata | `backend/evaluation.py` calculates metrics; `scripts/run_evaluations.py` runs the golden set and optional LangSmith experiment | `data/golden_dataset.jsonl` is the 20-case evaluation set | `tests/` covers database, API, agent, RAG, guardrails, memory, and UI |

Shared configuration is in `backend/settings.py`; copy `.env.example` to `.env` and set credentials locally. No credentials are needed to run tests or the SQLite demonstration.

## Run locally (Windows PowerShell)

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m scripts.init_db
```

In terminal 1, start the backend on loopback. Port `8017` is used because Windows environments may reserve common development ports:

```powershell
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8017
```

In terminal 2:

```powershell
streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. The backend health endpoint is `http://127.0.0.1:8017/health`; interactive API docs are at `http://127.0.0.1:8017/docs`.

The out-of-box database is local SQLite and includes a demo customer (`demo-customer`), sample product IDs (`LAPTOP-100`, `PHONE-200`), and order `ORD-DEMO-001`. Without provider credentials, policy answers use the bundled local sample policies and the agent identifies itself as `offline-demo`.

## Configure external services

1. **OpenAI:** Set `OPENAI_API_KEY` in `.env`. The simple model defaults to `gpt-4o-mini`, the complex model to `gpt-4o`, and embeddings to `text-embedding-3-small`.
2. **MySQL:** Create a database and least-privilege application user. Set `DATABASE_URL` to `mysql+pymysql://USER:PASSWORD@HOST:3306/ecomm_support`, then run `python -m scripts.init_db`. Do not give the application account schema-admin privileges in production.
3. **Pinecone:** Create a cosine index using the embedding model's 1,536 dimensions, then set `PINECONE_API_KEY`, `PINECONE_INDEX`, and optionally `PINECONE_NAMESPACE`. Ingest documents with `python -m scripts.ingest_policies`. A Pinecone index must use the same embedding model/dimension as ingestion.
4. **Upstash Redis:** Set `UPSTASH_REDIS_URL` to the Redis-compatible `rediss://` connection URL, not the REST endpoint/token pair. Local demo memory is process-local and is not durable across restarts.
5. **LangSmith:** Set `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, and `LANGSMITH_PROJECT`. Inputs/outputs passed to the agent trace are PII-redacted.

Never put live credentials in `.env.example`, source files, screenshots, or commits. The checked-in example contains blank values.

## Milestone commands

```powershell
# M1: create schema and demo rows; stdio MCP server is normally launched by the agent
python -m scripts.init_db
python -m backend.mcp_server

# M2: after configuring OpenAI + Pinecone
python -m scripts.ingest_policies
python -m scripts.benchmark_retrieval

# M3/M4: run the two local services in separate terminals as shown above

# M5: local golden evaluation (writes an ignored report under data/)
python -m scripts.run_evaluations
```

The retrieval benchmark reports mean Recall@k and mean reciprocal rank for all three strategies over the golden questions that have policy labels. LangSmith evaluation records tool-call accuracy, an LLM-judge hallucination rate when OpenAI is configured (otherwise a citation/source proxy), and response latency.

## Validation

```powershell
python -m pytest -q
```

## Important production gaps

- The demo customer ID field is not authentication. Production must derive the customer identity from a verified login/token and never accept an arbitrary customer ID from the browser.
- Ordering is a real write. Add a customer confirmation/approval flow, idempotency keys, payment integration controls, fraud checks, rate limits, and auditable authorization before exposing it publicly.
- Use TLS, managed secrets, database migrations, tenant isolation, least-privilege MySQL/Pinecone/Redis credentials, and retention/deletion policies.
- Lexical fallback is provided only for local demos. Production answers should use the configured retriever and must abstain when evidence is unavailable.
- The input guardrails are defense-in-depth, not a complete prompt-injection detector. Tool argument validation and database ownership checks remain mandatory.
