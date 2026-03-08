"""Enable PostgreSQL Row Level Security on all tenant-scoped tables.

Revision ID: 007
Revises: 006
Create Date: 2026-03-08

Creates two policies per table:
  - ``tenant_isolation``: restricts access to rows matching the
    ``app.current_tenant_id`` session variable set after authentication.
  - ``admin_bypass``: allows unrestricted access when
    ``app.rls_bypass`` is set to ``'on'`` (background jobs, migrations).

Note: RLS is enforced only for non-owner roles by default.  Production
deployments MUST use a dedicated application role that does not own the
tables (see docs/ARCHITECTURE.md § Tenant isolation).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RLS_TABLES = [
    "api_keys",
    "connector_instances",
    "credentials",
    "flows",
    "flow_executions",
    "field_mappings",
    "workflows",
    "workflow_executions",
    "sync_ledger",
]


def upgrade() -> None:
    for table in _RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
                FOR ALL
                USING (
                    current_setting('app.current_tenant_id', true) <> ''
                    AND tenant_id = current_setting('app.current_tenant_id', true)::uuid
                )
                WITH CHECK (
                    current_setting('app.current_tenant_id', true) <> ''
                    AND tenant_id = current_setting('app.current_tenant_id', true)::uuid
                )
        """)

        op.execute(f"""
            CREATE POLICY admin_bypass ON {table}
                FOR ALL
                USING (current_setting('app.rls_bypass', true) = 'on')
                WITH CHECK (current_setting('app.rls_bypass', true) = 'on')
        """)


def downgrade() -> None:
    for table in _RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS admin_bypass ON {table}")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
