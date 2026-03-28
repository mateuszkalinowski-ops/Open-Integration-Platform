"""Add sync_ledger table and sync_config column to workflows

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-25

Enables incremental data synchronization by tracking per-entity sync state
(content hash, status, retry count) and allowing workflows to define sync
configuration (entity key, mode, dedup strategy).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workflows",
        sa.Column("sync_config", postgresql.JSONB(), nullable=True),
    )

    op.create_table(
        "sync_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("source_connector", sa.String(100), nullable=False),
        sa.Column("source_event", sa.String(100), nullable=False),
        sa.Column("entity_key", sa.String(500), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("sync_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workflow_id", "entity_key", name="uq_sync_ledger_workflow_entity"),
    )
    op.create_index("ix_sync_ledger_lookup", "sync_ledger", ["workflow_id", "entity_key"])
    op.create_index("ix_sync_ledger_status", "sync_ledger", ["workflow_id", "sync_status"])


def downgrade() -> None:
    op.drop_index("ix_sync_ledger_status", table_name="sync_ledger")
    op.drop_index("ix_sync_ledger_lookup", table_name="sync_ledger")
    op.drop_table("sync_ledger")
    op.drop_column("workflows", "sync_config")
