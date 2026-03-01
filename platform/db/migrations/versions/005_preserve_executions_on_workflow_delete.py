"""Preserve workflow executions when workflow is deleted

Revision ID: 005
Revises: 004
Create Date: 2026-03-01

Changes workflow_executions.workflow_id from NOT NULL with CASCADE DELETE
to nullable with ON DELETE SET NULL. Adds workflow_name column so the
execution retains the workflow's name even after the workflow is deleted.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "workflow_executions",
        sa.Column("workflow_name", sa.String(300), nullable=True),
    )

    op.execute("""
        UPDATE workflow_executions we
        SET workflow_name = w.name
        FROM workflows w
        WHERE we.workflow_id = w.id AND we.workflow_name IS NULL
    """)

    op.drop_constraint(
        "workflow_executions_workflow_id_fkey",
        "workflow_executions",
        type_="foreignkey",
    )
    op.alter_column("workflow_executions", "workflow_id", nullable=True)
    op.create_foreign_key(
        "workflow_executions_workflow_id_fkey",
        "workflow_executions",
        "workflows",
        ["workflow_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.execute("DELETE FROM workflow_executions WHERE workflow_id IS NULL")

    op.drop_constraint(
        "workflow_executions_workflow_id_fkey",
        "workflow_executions",
        type_="foreignkey",
    )
    op.alter_column("workflow_executions", "workflow_id", nullable=False)
    op.create_foreign_key(
        "workflow_executions_workflow_id_fkey",
        "workflow_executions",
        "workflows",
        ["workflow_id"],
        ["id"],
    )

    op.drop_column("workflow_executions", "workflow_name")
