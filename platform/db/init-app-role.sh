#!/bin/bash
# Create a restricted application role for runtime database access.
#
# RLS policies are only enforced for non-owner roles; connecting as the
# table owner (pinquark) effectively bypasses RLS.  This script creates
# pinquark_app with the minimum privileges needed by the FastAPI runtime
# while leaving the owner role for migrations only.
#
# Mounted into the postgres container via docker-entrypoint-initdb.d/.
# Requires DB_APP_PASSWORD env var to be set in the postgres service.

set -e

if [ -z "${DB_APP_PASSWORD:-}" ]; then
    echo "WARNING: DB_APP_PASSWORD not set — skipping pinquark_app role creation."
    echo "RLS will NOT be enforced (app connects as table owner)."
    exit 0
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'pinquark_app') THEN
            CREATE ROLE pinquark_app LOGIN PASSWORD '${DB_APP_PASSWORD}';
        ELSE
            ALTER ROLE pinquark_app PASSWORD '${DB_APP_PASSWORD}';
        END IF;
    END
    \$\$;

    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO pinquark_app;
    GRANT USAGE ON SCHEMA public TO pinquark_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pinquark_app;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pinquark_app;

    ALTER DEFAULT PRIVILEGES FOR ROLE ${POSTGRES_USER} IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO pinquark_app;
    ALTER DEFAULT PRIVILEGES FOR ROLE ${POSTGRES_USER} IN SCHEMA public
        GRANT USAGE, SELECT ON SEQUENCES TO pinquark_app;
EOSQL

echo "Created/updated pinquark_app role with restricted privileges."
