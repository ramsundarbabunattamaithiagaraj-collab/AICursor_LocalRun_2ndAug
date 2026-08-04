# Developer Guide

## Coding Standards
- SOLID, DRY, KISS, YAGNI (per `retail_agend.md` Section 10).
- Full type hints on all function signatures.
- Business logic lives only in `services/`; routers stay thin; repositories stay
  query-only (no business rules).
- Never hardcode secrets — read from `app.core.config.get_settings()`, which
  overlays `.env` on top of `config/config.yaml` defaults.
- Every new domain error should extend `app.utils.exceptions.RetailIQError` so it is
  automatically translated to a clean HTTP 400 by the global exception handler (or
  add a specific `except` clause in the router for a more precise status code).

## Adding a New Resource (example: "Promotions")
1. **Model** — `app/models/promotion.py` (SQLAlchemy `Base` subclass).
2. **Register** the model import in `app/db/init_db.py`.
3. **Schema** — `app/schemas/promotion.py` (`PromotionCreate`, `PromotionRead`, ...).
4. **Repository** — `app/repositories/promotion_repository.py` extending
   `BaseRepository[Promotion]`.
5. **Service** — `app/services/promotion_service.py` with validation/business rules,
   raising `app.utils.exceptions` subclasses on failure.
6. **Router** — `app/api/v1/routers/promotions_router.py`, mapping exceptions to
   HTTP status codes; register it in `app/main.py`.
7. **Tests** — `tests/unit/test_promotion_service.py` (positive/negative/boundary)
   and `tests/integration/test_promotions_api.py`.
8. **Frontend** — add a Streamlit page or extend an existing one under
   `frontend/streamlit_app/pages/`.

## Adding a New Agent
1. Create `app/agents/<name>_agent.py` extending `BaseRetailAgent`, implementing
   `task_description()` and `fallback_output()`.
2. Register it in `AGENT_REGISTRY` in `app/agents/crew_config.py`.
3. It's automatically available via `/api/v1/agents/run` and the roster endpoint.

## MCP Server (Cursor / Claude Desktop integration)
`backend/mcp_server/server.py` is a small internal MCP (Model Context Protocol)
server that exposes core RetailIQ operations as tools any MCP-compatible AI
client can call — it imports `app.services.*` directly and talks straight to
the local SQLite DB (no need for the FastAPI server to be running).

Tools exposed: `search_products`, `get_product_by_sku`, `list_categories`,
`check_inventory`, `list_low_stock`, `place_order`, `get_order_status`,
`query_knowledge_base` (RAG), `run_sdlc_agent` (CrewAI).

**Install** (optional dependency, pinned to the stable MCP SDK 1.x line since
2.x requires a `starlette` version incompatible with our pinned FastAPI):
```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install "mcp[cli]==1.29.0" "starlette>=0.40,<0.42"
```
(Also included in `requirements-optional.txt`.)

**Run standalone** (stdio transport):
```powershell
cd backend
.\.venv\Scripts\python.exe -m mcp_server.server
```

**Use from Cursor**: already configured in `.cursor/mcp.json` at the repo root,
pointing at the backend venv's Python. Reload the MCP servers list in Cursor's
settings (or restart Cursor) to pick up the `retailiq` server and its tools.

**Adding a new tool**: add a `@mcp.tool()`-decorated function in
`backend/mcp_server/server.py` that opens a `SessionLocal()`, delegates to the
relevant `app.services.*` class, and returns a plain dict/list (JSON-
serializable). Keep business logic in the services layer — the MCP tool
functions should stay thin, mirroring the router pattern.

## Running Tests & Linters

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

## Configuration Reference
See `backend/config/config.yaml` for all tunables (server host/port, DB URL, JWT
expiry, RAG chunk size/overlap/top_k, CrewAI temperature/retry/max_iterations,
logging level/rotation). Secrets (`SECRET_KEY`, `DATABASE_URL` override,
`OPENAI_API_KEY`) come from `.env` — see `backend/.env.example`.

## Project Conventions
- Exceptions: raise `app.utils.exceptions.*`, never bare `Exception`, never swallow
  errors silently (Section 10: "Never ... Ignore exceptions").
- Logging: use `app.core.logging_config.get_logger(__name__)`; never `print()`.
- Responses: prefer the `success_response()` envelope for ad-hoc endpoints; resource
  endpoints return Pydantic response models directly for clean OpenAPI schemas.
