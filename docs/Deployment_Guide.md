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
4. Python version: the root-level `runtime.txt` (`python-3.12`) pins Cloud to
   a well-supported interpreter. Without it, Cloud may default to a very new
   Python release for which packages like `pandas`/`numpy` have no prebuilt
   wheel yet, forcing a slow (multi-minute, sometimes failing) source build
   on every fresh deploy.

### Why the app feels slow to load
- **First deploy / after a dependency change**: Cloud has to `pip install`
  from scratch — normal, one-time, a few minutes. Subsequent visits reuse the
  cached environment and start almost instantly.
- **App put to sleep from inactivity**: free Community Cloud apps sleep after
  a period with no visitors; the next visit triggers a ~30-60s wake-up. This
  is a one-time cost per sleep cycle, not a persistent slowdown.
- **Backend cold start (most common cause)**: if the FastAPI backend is on a
  free tier (e.g. Render's free plan), it also sleeps after ~15 minutes idle
  and takes 30-60s to wake on the next request. `Home.py`'s health check
  (`is_backend_reachable`, cached for 15s to avoid hammering the backend on
  every Streamlit rerun) will show a "cold-starting" warning with a Retry
  button in this case rather than hanging silently.
- **Fix**: keep the backend (and optionally the Streamlit app) warm with a
  scheduled ping. This repo includes a ready-to-use
  [`.github/workflows/keep-alive.yml`](../.github/workflows/keep-alive.yml)
  that pings both every 10 minutes for free — just set the `BACKEND_HEALTH_URL`
  and/or `FRONTEND_URL` repo variables (Settings → Secrets and variables →
  Actions → Variables) to your deployed URLs. Alternatively use an external
  scheduler like [cron-job.org](https://cron-job.org)/UptimeRobot, or upgrade
  to an always-on paid tier if consistent low latency matters.

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
