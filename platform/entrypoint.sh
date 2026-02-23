#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Running database migrations..."
python -m db.init_db

echo "[entrypoint] Starting platform API..."
exec uvicorn api.gateway:app --host 0.0.0.0 --port 8080
