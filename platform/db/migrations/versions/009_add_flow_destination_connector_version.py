"""Add destination_connector_version column to flows table.

Revision ID: 0009
Revises: 0008
Create Date: 2026-03-08

Stores the pinned connector version for flow destinations,
enabling deterministic version selection in the Flow Engine.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "flows",
        sa.Column("destination_connector_version", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("flows", "destination_connector_version")
