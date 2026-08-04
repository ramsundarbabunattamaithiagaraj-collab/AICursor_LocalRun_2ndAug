# RetailIQ Platform

An enterprise retail operations platform combining a traditional FastAPI/Streamlit
e-commerce backend (catalog, inventory, orders, customers/loyalty, JWT auth) with an
AI layer: a document RAG (Retrieval-Augmented Generation) knowledge assistant and a
CrewAI-powered multi-agent SDLC toolkit (Business Analyst, Architect, Developer,
Tester, Documentation agents).

Generated from the project specification in [`retail_agend.md`](./retail_agend.md).
See [`docs/`](./docs) for full documentation (architecture, API guide, installation,
deployment, user manual, developer guide, release notes, and BRD/FRD/SRS).

## Quick Start (Windows / PowerShell)

```powershell
# 1. Backend
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe seed_data.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# 2. Frontend (new terminal)
cd frontend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe -m streamlit run streamlit_app/Home.py
```

- Backend API: http://localhost:8000 (interactive docs at `/docs`)
- Frontend UI: http://localhost:8501
- Default admin login: `admin` / `Admin@123` (change immediately in production)

Full step-by-step instructions: [`docs/Installation_Guide.md`](./docs/Installation_Guide.md).

### Optional: MCP server (AI tool access for Cursor / Claude Desktop)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-optional.txt   # includes mcp[cli]
```

Already registered in `.cursor/mcp.json` — reload MCP servers in Cursor's
settings to pick up the `retailiq` tools (product search, inventory, orders,
RAG queries, SDLC agents). See [`docs/Developer_Guide.md`](./docs/Developer_Guide.md#mcp-server-cursor--claude-desktop-integration)
for details.

## Project Structure

```
Retail_Domain/
├── backend/            FastAPI application, services, RAG, CrewAI agents, tests
│   └── mcp_server/     Internal MCP server exposing platform ops as AI tools
├── frontend/           Streamlit multi-page UI
├── docs/               All generated documentation & specifications
├── .cursor/mcp.json    Registers the RetailIQ MCP server with Cursor
├── docker-compose.yml  One-command local orchestration
└── retail_agend.md     Source project specification
```

## Technology Stack (per specification defaults)

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI |
| Frontend | Streamlit |
| Database | SQLite (SQLAlchemy ORM) |
| Auth | JWT (python-jose + passlib/bcrypt) |
| AI Framework | CrewAI (graceful fallback without an LLM key) |
| Vector DB | ChromaDB when installed; built-in NumPy vector store otherwise |
| Testing | pytest |
| Container | Docker / docker-compose |
| Config | YAML (`backend/config/config.yaml`) + `.env` |
| AI tool access | Internal MCP server (`backend/mcp_server/`, MCP SDK 1.x) |

## Notable Engineering Decisions

- **Graceful degradation everywhere.** The platform is designed to run out of the
  box with zero external API keys and no compiled/native dependencies. Heavier
  production upgrades (ChromaDB, sentence-transformers/BAAI embeddings, real
  LLM-backed CrewAI agents) are available via `backend/requirements-optional.txt`
  and are auto-detected at runtime.
- See [`docs/Architecture.md`](./docs/Architecture.md) for the full rationale.
