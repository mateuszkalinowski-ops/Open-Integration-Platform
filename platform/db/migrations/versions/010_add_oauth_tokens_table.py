"""Add oauth_tokens table for OAuth2 lifecycle management.

Revision ID: 0010
Revises: 0009
Create Date: 2026-03-11

Stores encrypted OAuth2 tokens with refresh tracking and expiry.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oauth_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("connector_name", sa.String(100), nullable=False),
        sa.Column("credential_name", sa.String(100), nullable=False, server_default="default"),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("access_token_encrypted", sa.Text, nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text, nullable=True),
        sa.Column("token_type", sa.String(20), nullable=False, server_default="bearer"),
        sa.Column("scope", sa.Text, nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refresh_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_oauth_tokens_tenant_connector", "oauth_tokens", ["tenant_id", "connector_name"])
    op.create_index("ix_oauth_tokens_expires_at", "oauth_tokens", ["expires_at"])
    op.create_index("ix_oauth_tokens_status", "oauth_tokens", ["status"])

    op.execute("ALTER TABLE oauth_tokens ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON oauth_tokens
        FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)
    op.execute("""
        CREATE POLICY admin_bypass ON oauth_tokens
        FOR ALL USING (current_setting('app.rls_bypass', true) = 'on')
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS admin_bypass ON oauth_tokens")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON oauth_tokens")
    op.drop_index("ix_oauth_tokens_status")
    op.drop_index("ix_oauth_tokens_expires_at")
    op.drop_index("ix_oauth_tokens_tenant_connector")
    op.drop_table("oauth_tokens")
