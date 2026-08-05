#!/bin/sh
# Container entrypoint: seeds demo data (idempotent - skips if already
# seeded) then starts the API, binding to $PORT if the host provides one
# (Render/Railway/etc. assign a dynamic port; defaults to 8000 otherwise).
set -e

python seed_data.py

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
