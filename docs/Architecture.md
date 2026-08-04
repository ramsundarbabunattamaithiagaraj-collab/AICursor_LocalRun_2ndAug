# Architecture Document

## 1. Overview

```
┌─────────────────────┐        HTTP/JSON        ┌──────────────────────────────────┐
│   Streamlit UI       │ ───────────────────────▶ │           FastAPI App            │
│  (frontend/)          │ ◀─────────────────────── │            (backend/)            │
└─────────────────────┘                          │                                    │
                                                  │  Routers (api/v1/routers)          │
                                                  │        │                            │
                                                  │        ▼                            │
                                                  │  Services (business logic)          │
                                                  │        │                            │
                                                  │        ▼                            │
                                                  │  Repositories (data access)         │
                                                  │        │                            │
                                                  │        ▼                            │
                                                  │  SQLAlchemy ORM Models              │
                                                  │        │                            │
                                                  │        ▼                            │
                                                  │      SQLite (data/retailiq.db)      │
                                                  │                                    │
                                                  │  RAG: PdfExtraction → Embedding →   │
                                                  │       VectorStore (Chroma/NumPy)     │
                                                  │                                    │
                                                  │  Agents: CrewAI 5-agent SDLC crew   │
                                                  │       (BA/Architect/Dev/Test/Docs)  │
                                                  └──────────────────────────────────┘
```

## 2. Layered Backend Design
- **`api/v1/routers/`** — HTTP concerns only: request/response models, status codes,
  exception → HTTP translation. No business logic.
- **`services/`** — business rules, validation, orchestration across repositories.
  This is where SOLID/DRY/KISS are enforced (e.g. `OrderService` owns the order
  status state machine; `InventoryService` owns stock-reservation logic).
- **`repositories/`** — thin SQLAlchemy query wrappers extending a generic
  `BaseRepository[ModelType]` (Repository Pattern), keeping ORM query code out of
  services and enabling easy swapping/mocking in tests.
- **`models/`** — SQLAlchemy declarative ORM models (`Category`, `Product`,
  `Inventory`, `Customer`, `Order`/`OrderItem`, `User`, `RagDocument`,
  `FeedbackRecord`).
- **`schemas/`** — Pydantic request/response contracts, decoupled from ORM models.
- **`core/`** — configuration (`config.yaml` + `.env` overlay), logging, JWT/password
  security utilities.
- **`utils/`** — cross-cutting exception hierarchy and a standard API response
  envelope.

Dependency Injection is achieved via FastAPI's `Depends()` (e.g. `get_db`,
`get_current_user`) and by services/repositories accepting a `Session` in their
constructor rather than importing a global session.

## 3. Database Design

```
Category 1───* Product 1───* Inventory
Customer 1───* Order 1───* OrderItem *───1 Product
User (auth only, independent of Customer)
RagDocument (RAG ingestion metadata)
FeedbackRecord (Section 14 feedback)
```

Key fields per entity are documented inline in `backend/app/models/*.py`. SQLite is
the default (per spec); because access is entirely through SQLAlchemy Core/ORM, a
production deployment can switch to PostgreSQL by changing `DATABASE_URL` only.

## 4. RAG Subsystem
1. **Ingestion** (`PdfExtractionService`): a layout-aware pass over each PDF using
   `pdfplumber` (text + tables) and `PyMuPDF` (embedded images), tagging every chunk
   with its content type (`text`/`table`/`image`) and source page. Tables are kept as
   pipe-delimited structured rows (not flattened prose) so numeric fields stay
   queryable. If a page has no extractable text, an OCR fallback
   (`pytesseract` + Pillow) is attempted.
2. **Chunking & Embedding** (`RagService`, `EmbeddingService`): text is chunked using
   the configured `chunk_size`/`chunk_overlap` (defaults: 800/100). Embeddings are
   produced by the configured model (default `BAAI/bge-base-en-v1.5` via
   `sentence-transformers`) when the optional heavy dependency is installed;
   otherwise a deterministic lightweight hashing embedding is used so the pipeline
   never breaks.
3. **Storage & Retrieval**: embeddings are stored in ChromaDB when installed,
   otherwise in a built-in `SimpleVectorStore` (NumPy cosine similarity, JSON
   persistence) with an identical `add`/`query` interface — see the ADR below.
4. **Answering**: `RagService.query()` retrieves the top-k chunks, returns cited
   sources with a similarity score, and synthesizes an extractive answer. When a real
   LLM is configured, the AI Agents Studio can be used for generative synthesis
   instead.

### ADR: ChromaDB vs. built-in vector store
Older `chromadb` releases (0.5.x) default to a local index backed by
`chroma-hnswlib`, a compiled C++ extension with no prebuilt `cp312-win_amd64`
wheel, requiring a full Visual C++ Build Tools installation on Windows +
Python 3.12. Modern `chromadb` releases (>=1.x, pinned in
`requirements-optional.txt`) no longer require that compiled extension and
install cleanly from prebuilt wheels. To keep the *base* `pip install -r
requirements.txt` as lean and dependency-free as possible regardless of which
chromadb generation is available, ChromaDB remains an **optional** dependency.
`RagService` auto-detects it at startup and falls back to a pure-Python
`SimpleVectorStore` with the same interface otherwise. Both paths are
exercised by the same code — only the backing store differs. In this
environment, installing `crewai` (for LLM-backed agents) transitively pulled
in modern `chromadb`, which `RagService` picked up automatically on restart.

## 5. AI Agents Studio (CrewAI)
Each agent (`app/agents/*.py`) defines a `role`, `goal`, `backstory`, task
description, and a deterministic `fallback_output`. `AgentOrchestrationService`:
- Checks whether `OPENAI_API_KEY` is set **and** `crewai` is importable.
- If yes, builds a CrewAI `Agent`/`Task`/`Crew` (sequential process) backed by
  `ChatOpenAI` and executes it.
- If no (the default, zero-config case), returns the agent's fallback output,
  clearly labeled as simulated, so the studio is always usable in demos and CI.
- Computes heuristic quality metrics (confidence, hallucination risk, requirement
  coverage, context relevance, completeness) with an explanation string, per
  Section 15 of the specification.

## 6. Security Architecture
- Passwords: bcrypt via `passlib`.
- Sessions: stateless JWT bearer tokens (`python-jose`), configurable expiry.
- Authorization: `require_role(*roles)` FastAPI dependency for role-gated endpoints.
- Secrets: `.env` (never committed — see `.env.example`), overlaying non-secret
  defaults in `config/config.yaml`.
- Input validation: Pydantic schemas on every request body/query param, with
  field-level constraints (min/max length, numeric ranges, regex-constrained enums).

## 7. Deployment Architecture
- **Local dev**: two Python virtual environments (`backend/.venv`,
  `frontend/.venv`), run via `uvicorn` and `streamlit run`.
- **Containerized**: `backend/Dockerfile` + `frontend/Dockerfile` +
  root `docker-compose.yml` for one-command orchestration (see
  [Deployment Guide](./Deployment_Guide.md)).
- **Data persistence**: SQLite file and vector store data live under
  `backend/data/`, mounted as a volume in Docker so data survives container
  restarts.

## 8. Observability
Every HTTP request is logged (method, path, status, latency) via FastAPI
middleware. Every agent run logs agent name, input/output size, execution time, and
confidence. Logs go to both console and a rotating file
(`backend/logs/retailiq.log`, configurable size/backup count).
