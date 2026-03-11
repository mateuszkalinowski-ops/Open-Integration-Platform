"""Add webhook_events table for webhook ingestion service.

Revision ID: 011
Revises: 010
Create Date: 2026-03-11

Stores received webhook events with signature validation and processing status.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "webhook_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("connector_name", sa.String(100), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("external_id", sa.String(500), nullable=True),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("headers", JSONB, nullable=True),
        sa.Column("signature_valid", sa.Boolean, nullable=True),
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="received"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_webhook_events_tenant_connector", "webhook_events", ["tenant_id", "connector_name"])
    op.create_index("ix_webhook_events_external_id", "webhook_events", ["external_id"])
    op.create_index("ix_webhook_events_status", "webhook_events", ["processing_status"])
    op.create_index("ix_webhook_events_received_at", "webhook_events", ["received_at"])

    op.execute("ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON webhook_events
        FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)
    op.execute("""
        CREATE POLICY admin_bypass ON webhook_events
        FOR ALL USING (current_setting('app.rls_bypass', true) = 'on')
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS admin_bypass ON webhook_events")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON webhook_events")
    op.drop_index("ix_webhook_events_received_at")
    op.drop_index("ix_webhook_events_status")
    op.drop_index("ix_webhook_events_external_id")
    op.drop_index("ix_webhook_events_tenant_connector")
    op.drop_table("webhook_events")
