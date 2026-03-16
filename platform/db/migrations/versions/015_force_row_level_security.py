"""Force RLS on all tenant-scoped tables.

Revision ID: 015
Revises: 014
Create Date: 2026-03-16

ENABLE ROW LEVEL SECURITY allows the table owner to bypass policies.
FORCE ROW LEVEL SECURITY ensures policies apply even to the table
owner, which is a hard requirement when the application role happens
to own tables or when connections as the owner leak into runtime.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "015"
down_revision: str | None = "014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ALL_RLS_TABLES = [
    "connector_instances",
    "credentials",
    "flows",
    "flow_executions",
    "field_mappings",
    "workflows",
    "workflow_executions",
    "sync_ledger",
    "oauth_tokens",
    "webhook_events",
    "audit_log",
    "workflow_versions",
    "credential_tokens",
]


def upgrade() -> None:
    for table in _ALL_RLS_TABLES:
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in _ALL_RLS_TABLES:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
