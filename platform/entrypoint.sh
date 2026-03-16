#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Running database migrations..."
python -m db.init_db

if [ -n "${DATABASE_APP_URL:-}" ]; then
    echo "[entrypoint] Switching to app role for runtime (RLS enforced)..."
    export DATABASE_URL="$DATABASE_APP_URL"
fi

echo "[entrypoint] Starting platform API..."
exec uvicorn api.gateway:app --host 0.0.0.0 --port 8080 \
  --proxy-headers \
  --forwarded-allow-ips "${TRUSTED_PROXY_IPS:-127.0.0.1}"
