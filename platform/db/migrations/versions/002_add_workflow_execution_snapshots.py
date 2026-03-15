"""Add workflow_nodes_snapshot and workflow_edges_snapshot to workflow_executions

Revision ID: 002
Revises: 001
Create Date: 2026-02-24

Stores a copy of the workflow graph (nodes + edges) at execution time so
the execution detail view can render the graph even if the workflow
definition is later modified or deleted.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("workflow_executions")}

    if "workflow_nodes_snapshot" not in existing:
        op.add_column(
            "workflow_executions",
            sa.Column("workflow_nodes_snapshot", postgresql.JSONB(), nullable=True),
        )
    if "workflow_edges_snapshot" not in existing:
        op.add_column(
            "workflow_executions",
            sa.Column("workflow_edges_snapshot", postgresql.JSONB(), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("workflow_executions", "workflow_edges_snapshot")
    op.drop_column("workflow_executions", "workflow_nodes_snapshot")
