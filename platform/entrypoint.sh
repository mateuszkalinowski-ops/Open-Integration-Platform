#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Running database migrations..."
python -m db.init_db

if [ -n "${DATABASE_APP_URL:-}" ]; then
    APP_HOST=$(echo "$DATABASE_APP_URL" | sed -n 's|.*@\([^:/]*\).*|\1|p')
    APP_PORT=$(echo "$DATABASE_APP_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    APP_PORT="${APP_PORT:-5432}"
    if python -c "
import asyncio, sys
async def check():
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        e = create_async_engine('${DATABASE_APP_URL}', pool_pre_ping=True)
        async with e.connect() as c:
            await c.execute(__import__('sqlalchemy').text('SELECT 1'))
        await e.dispose()
    except Exception as exc:
        print(f'[entrypoint] WARNING: app role connection failed: {exc}', file=sys.stderr)
        sys.exit(1)
asyncio.run(check())
" 2>&1; then
        echo "[entrypoint] Switching to app role for runtime (RLS enforced)..."
        export DATABASE_URL="$DATABASE_APP_URL"
    else
        echo "[entrypoint] WARNING: Keeping owner role — set DB_APP_PASSWORD secret to enable RLS app role"
    fi
fi

echo "[entrypoint] Starting platform API..."
exec uvicorn api.gateway:app --host 0.0.0.0 --port 8080 \
  --proxy-headers \
  --forwarded-allow-ips "${TRUSTED_PROXY_IPS:-127.0.0.1}"
