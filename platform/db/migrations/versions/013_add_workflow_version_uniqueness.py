"""Enforce unique workflow version numbers per workflow.

Revision ID: 0013
Revises: 0012
Create Date: 2026-03-11
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_workflow_versions_workflow_version",
        "workflow_versions",
        ["workflow_id", "version"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_workflow_versions_workflow_version",
        "workflow_versions",
        type_="unique",
    )
