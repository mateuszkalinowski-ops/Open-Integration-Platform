"""Fix tenant_isolation RLS policies to handle missing/empty GUC safely.

Revision ID: 017
Revises: 016
Create Date: 2026-03-20

Several tenant_isolation policies used ``current_setting('app.current_tenant_id')``
without ``missing_ok=true``, causing crashes when the GUC was absent (e.g. background
tasks using only ``rls_bypass``).  Others used the ``true`` flag but still crashed
when the GUC value was an empty string after a transaction commit (``''::uuid`` fails).

This migration recreates ALL tenant_isolation policies with a safe expression:

    NULLIF(current_setting('app.current_tenant_id', true), '') IS NOT NULL
    AND tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid

``NULLIF`` converts both NULL and empty string to NULL, and ``NULL::uuid`` is valid
(returns NULL), so the cast never crashes regardless of GUC state.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "017"
down_revision: str | None = "016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TENANT_TABLES = [
    "audit_log",
    "connector_instances",
    "credential_tokens",
    "credentials",
    "field_mappings",
    "flow_executions",
    "flows",
    "oauth_tokens",
    "sync_ledger",
    "webhook_events",
    "workflow_executions",
    "workflow_versions",
    "workflows",
]

_SAFE_POLICY = """
    CREATE POLICY tenant_isolation ON {table}
    FOR ALL USING (
        NULLIF(current_setting('app.current_tenant_id', true), '') IS NOT NULL
        AND tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
    )
"""


def upgrade() -> None:
    for table in _TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(_SAFE_POLICY.format(table=table))


def downgrade() -> None:
    for table in _TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            FOR ALL USING (
                current_setting('app.current_tenant_id', true) <> ''
                AND tenant_id = current_setting('app.current_tenant_id', true)::uuid
            )
        """)
