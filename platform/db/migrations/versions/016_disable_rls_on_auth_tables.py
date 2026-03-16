"""Disable RLS on authentication lookup tables.

Revision ID: 016
Revises: 015
Create Date: 2026-03-16

api_keys and tenants are queried during authentication *before* the
tenant identity is known.  Having RLS on these tables creates a
chicken-and-egg problem: you need to read api_keys to discover the
tenant, but RLS blocks the read because no tenant context is set.

This migration drops any RLS policies and disables RLS on both tables
so the auth flow works regardless of the database role.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "016"
down_revision: str | None = "015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_AUTH_TABLES = ["api_keys", "tenants"]


def upgrade() -> None:
    for table in _AUTH_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"DROP POLICY IF EXISTS admin_bypass ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in _AUTH_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
