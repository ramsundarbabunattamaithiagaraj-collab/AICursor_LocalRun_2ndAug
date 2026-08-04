# Installation Guide

## Prerequisites
- Python 3.12 (or 3.11+) on PATH
- Windows PowerShell (or any shell — commands below use PowerShell syntax)
- No compiled build toolchain required for the default install

## 1. Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` if needed (defaults work out of the box):

```
SECRET_KEY=change-this-to-a-long-random-secret-in-production
DATABASE_URL=sqlite:///./data/retailiq.db
OPENAI_API_KEY=            # optional - only needed for real LLM-backed agents
```

Seed demo data (categories, products, inventory, customers, a default admin user):

```powershell
.\.venv\Scripts\python.exe seed_data.py
```

Run the API server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- API root: http://localhost:8000
- Interactive docs (Swagger UI): http://localhost:8000/docs
- Health check: http://localhost:8000/health

## 2. Frontend Setup

In a new terminal:

```powershell
cd frontend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe -m streamlit run streamlit_app/Home.py
```

- UI: http://localhost:8501
- Default login (from seed data): username `admin`, password `Admin@123`

## 3. Running Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

Coverage report:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

## 4. Optional: Production-Grade AI Capabilities

By default the platform runs with zero external dependencies/API keys:
- RAG uses a built-in NumPy vector store and a lightweight hashing embedding.
- AI Agents Studio returns clearly-labeled deterministic template output.

To enable the full stack described in the specification:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-optional.txt
```

Then add to `.env` (Groq is preferred when set; falls back to OpenAI otherwise):

```
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...
```

> `requirements-optional.txt` pins a modern `chromadb` (>=1.x) that installs from
> prebuilt wheels with no compiled toolchain needed on Windows + Python 3.12. If
> you ever pull in an older `chromadb` (<1.0) transitively, its `chroma-hnswlib`
> dependency has no `cp312-win_amd64` wheel and needs Microsoft C++ Build Tools
> ("Desktop development with C++" workload) or Python 3.11 instead.

## 5. Docker (Alternative)

```powershell
docker compose up --build
```

See [Deployment Guide](./Deployment_Guide.md) for details.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `Cannot reach the backend API` on Home page | Ensure `uvicorn` is running on port 8000 and `frontend/.env`'s `API_BASE_URL` matches. |
| `bcrypt` version warning on startup | Harmless; caused by `passlib` probing a newer `bcrypt`. Already pinned to a compatible version in `requirements.txt`. |
| PDF ingestion returns 0 chunks | Ensure the PDF isn't empty/corrupt; scanned PDFs need `pytesseract` + a system Tesseract install for OCR. |
| Agents Studio output says "simulated" | Expected without `OPENAI_API_KEY` + `crewai` installed — see Section 4 above. |
