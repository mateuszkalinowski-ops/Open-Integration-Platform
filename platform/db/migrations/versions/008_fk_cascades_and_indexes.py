"""Fix FK cascades, add missing indexes, drop redundant index.

Revision ID: 008
Revises: 007
Create Date: 2026-03-08

- flow_executions.flow_id: add ON DELETE SET NULL (consistent with workflow_executions)
- sync_ledger.workflow_id: add ON DELETE CASCADE (sync state is meaningless without workflow)
- Add indexes on flow_executions.flow_id and workflow_executions.workflow_id
- Drop redundant ix_sync_ledger_lookup (duplicate of unique constraint index)
"""
from typing import Sequence, Union

from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("flow_executions_flow_id_fkey", "flow_executions", type_="foreignkey")
    op.create_foreign_key(
        "flow_executions_flow_id_fkey",
        "flow_executions",
        "flows",
        ["flow_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column("flow_executions", "flow_id", nullable=True)

    op.drop_constraint("sync_ledger_workflow_id_fkey", "sync_ledger", type_="foreignkey")
    op.create_foreign_key(
        "sync_ledger_workflow_id_fkey",
        "sync_ledger",
        "workflows",
        ["workflow_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index("ix_flow_executions_flow_id", "flow_executions", ["flow_id"])
    op.create_index("ix_workflow_executions_workflow_id", "workflow_executions", ["workflow_id"])

    op.drop_index("ix_sync_ledger_lookup", table_name="sync_ledger")


def downgrade() -> None:
    op.create_index("ix_sync_ledger_lookup", "sync_ledger", ["workflow_id", "entity_key"])

    op.drop_index("ix_workflow_executions_workflow_id", table_name="workflow_executions")
    op.drop_index("ix_flow_executions_flow_id", table_name="flow_executions")

    op.drop_constraint("sync_ledger_workflow_id_fkey", "sync_ledger", type_="foreignkey")
    op.create_foreign_key(
        "sync_ledger_workflow_id_fkey",
        "sync_ledger",
        "workflows",
        ["workflow_id"],
        ["id"],
    )

    op.alter_column("flow_executions", "flow_id", nullable=False)
    op.drop_constraint("flow_executions_flow_id_fkey", "flow_executions", type_="foreignkey")
    op.create_foreign_key(
        "flow_executions_flow_id_fkey",
        "flow_executions",
        "flows",
        ["flow_id"],
        ["id"],
    )
