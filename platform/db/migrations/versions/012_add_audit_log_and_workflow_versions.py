"""Add audit_log and workflow_versions tables.

Revision ID: 012
Revises: 011
Create Date: 2026-03-11

Audit trail for all entity mutations and snapshot-based workflow versioning.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "012"
down_revision: str | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(100), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("old_value", JSONB, nullable=True),
        sa.Column("new_value", JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_tenant_entity", "audit_log", ["tenant_id", "entity_type", "entity_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    op.create_table(
        "workflow_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workflow_id", UUID(as_uuid=True), sa.ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("nodes", JSONB, nullable=False),
        sa.Column("edges", JSONB, nullable=False),
        sa.Column("variables", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_workflow_versions_workflow", "workflow_versions", ["workflow_id", "version"])

    for table in ("audit_log", "workflow_versions"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
        """)
        op.execute(f"""
            CREATE POLICY admin_bypass ON {table}
            FOR ALL USING (current_setting('app.rls_bypass', true) = 'on')
        """)


def downgrade() -> None:
    for table in ("workflow_versions", "audit_log"):
        op.execute(f"DROP POLICY IF EXISTS admin_bypass ON {table}")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")

    op.drop_index("ix_workflow_versions_workflow")
    op.drop_table("workflow_versions")
    op.drop_index("ix_audit_log_created_at")
    op.drop_index("ix_audit_log_tenant_entity")
    op.drop_table("audit_log")
