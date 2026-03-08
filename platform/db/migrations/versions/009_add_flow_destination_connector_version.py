"""Add destination_connector_version column to flows table.

Revision ID: 009
Revises: 008
Create Date: 2026-03-08

Stores the pinned connector version for flow destinations,
enabling deterministic version selection in the Flow Engine.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "flows",
        sa.Column("destination_connector_version", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("flows", "destination_connector_version")
