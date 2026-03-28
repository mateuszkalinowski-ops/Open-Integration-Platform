"""Add credential_tokens table for opaque credential references.

Revision ID: 0014
Revises: 0013
Create Date: 2026-03-15

Maps each credential set (tenant + connector + credential_name) to an opaque
token so that GET responses never expose actual credential values.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "credential_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("connector_name", sa.String(100), nullable=False),
        sa.Column("credential_name", sa.String(100), nullable=False, server_default="default"),
        sa.Column("token", sa.String(64), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "tenant_id", "connector_name", "credential_name", name="uq_credential_tokens_tenant_connector_cred"
        ),
    )
    op.create_index("ix_credential_tokens_token", "credential_tokens", ["token"])
    op.create_index("ix_credential_tokens_tenant_connector", "credential_tokens", ["tenant_id", "connector_name"])

    op.execute("ALTER TABLE credential_tokens ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON credential_tokens
        FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)
    op.execute("""
        CREATE POLICY admin_bypass ON credential_tokens
        FOR ALL USING (current_setting('app.rls_bypass', true) = 'on')
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS admin_bypass ON credential_tokens")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON credential_tokens")
    op.drop_index("ix_credential_tokens_tenant_connector")
    op.drop_index("ix_credential_tokens_token")
    op.drop_table("credential_tokens")
