"""Add verification_reports and verification_settings tables

Revision ID: 003
Revises: 002
Create Date: 2026-02-24

Tables for the Verification Agent: stores periodic E2E test results
and scheduler configuration.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "verification_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("connector_name", sa.String(100), nullable=False),
        sa.Column("connector_version", sa.String(20), nullable=False),
        sa.Column("connector_category", sa.String(50), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("checks", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("summary", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_verification_reports_connector", "verification_reports", ["connector_name"])
    op.create_index("ix_verification_reports_status", "verification_reports", ["status"])
    op.create_index("ix_verification_reports_created", "verification_reports", ["created_at"])

    op.create_table(
        "verification_settings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("interval_days", sa.Integer, nullable=False, server_default=sa.text("7")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("verification_settings")
    op.drop_index("ix_verification_reports_created", table_name="verification_reports")
    op.drop_index("ix_verification_reports_status", table_name="verification_reports")
    op.drop_index("ix_verification_reports_connector", table_name="verification_reports")
    op.drop_table("verification_reports")
