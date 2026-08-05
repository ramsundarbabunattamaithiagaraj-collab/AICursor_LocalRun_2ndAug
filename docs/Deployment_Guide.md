# Deployment Guide

## Local Docker Compose

```powershell
docker compose up --build
```

This builds and runs two containers:
- `retailiq-backend` — FastAPI + Uvicorn on port 8000, with `backend/data` and
  `backend/logs` mounted as volumes so the SQLite DB, vector store, and logs persist
  across restarts.
- `retailiq-frontend` — Streamlit on port 8501, configured with
  `API_BASE_URL=http://backend:8000` to reach the backend over the Docker network.

Seed the database once the backend container is up:

```powershell
docker compose exec backend python seed_data.py
```

## Streamlit Community Cloud (Frontend Only)
Streamlit Cloud hosts only the Streamlit process — the FastAPI backend must be
deployed separately (Render/Railway/Fly.io/a VM, using `backend/Dockerfile`)
and reachable over HTTPS first.

1. Push to GitHub, then create an app at [share.streamlit.io](https://share.streamlit.io)
   pointing at:
   - Repository/branch: your repo / `main`
   - Main file path: `frontend/streamlit_app/Home.py`
2. In "Advanced settings" → Secrets, set:
   ```toml
   API_BASE_URL = "https://<your-hosted-backend-url>"
   ```
   (Cloud exposes top-level Secrets keys as `os.environ` too, so
   `api_client.py`'s `os.getenv("API_BASE_URL", ...)` picks it up with no
   code changes.)
3. Dependencies: **Cloud only auto-installs a `requirements.txt` found at the
   repo root or in the exact same directory as the entry-point file** — never
   from an intermediate ancestor folder. Since the entry point is
   `frontend/streamlit_app/Home.py` but the dependencies live in
   `frontend/requirements.txt` (one level above that script's own directory),
   Cloud would silently skip them, install bare Streamlit only, and crash
   with `ModuleNotFoundError` (`dotenv`, `requests`, `pandas`, ...). The
   root-level `requirements.txt` in this repo exists specifically to fix
   that — keep it in sync with `frontend/requirements.txt` if you add new
   frontend dependencies.

## Environment Variables (Production)
Set these via your orchestrator's secret management (never commit `.env`):

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | JWT signing secret — use a long random value |
| `DATABASE_URL` | e.g. `postgresql+psycopg://user:pass@host:5432/retailiq` for production scale |
| `OPENAI_API_KEY` | Enables real LLM-backed CrewAI agents (optional) |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |

## Scaling Notes
- The FastAPI app is stateless aside from the SQLite file and vector store data —
  scale horizontally behind a load balancer once migrated to a networked database
  (PostgreSQL) and a networked vector store (managed ChromaDB/Pinecone/etc.).
- Run Uvicorn with multiple workers in production:
  `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`.
- Put a reverse proxy (nginx/Caddy) in front of both services for TLS termination.

## Health Checks
- Backend: `GET /health` → `{"success": true, "data": {"status": "healthy"}}`
- Frontend: Streamlit's built-in `/_stcore/health` endpoint.

## Rollback Strategy
- The SQLite DB file (`backend/data/retailiq.db`) and vector store directory
  (`backend/data/chroma` or `backend/data/simple_store.json`) should be backed up
  before any deployment. Since the schema is managed by `init_db()`
  (`Base.metadata.create_all`), additive schema changes are safe; destructive changes
  should ship with an explicit migration script (a future Alembic integration is a
  natural extension point).
