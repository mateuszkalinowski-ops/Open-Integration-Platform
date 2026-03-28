"""Add indexes on tenant_id for all tenant-scoped tables.

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-08

Adds btree indexes on tenant_id columns to improve query performance
for per-tenant data access patterns.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = [
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
    for table in _TABLES:
        op.create_index(
            f"ix_{table}_tenant_id",
            table,
            ["tenant_id"],
        )


def downgrade() -> None:
    for table in _TABLES:
        op.drop_index(f"ix_{table}_tenant_id", table_name=table)
