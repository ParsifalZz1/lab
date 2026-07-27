"""Add schedule assignment records.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assignments",
        sa.Column("assignment_id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.run_id"), nullable=False),
        sa.Column("task_id", sa.String(64), sa.ForeignKey("task_nodes.task_id"), nullable=False),
        sa.Column("worker_id", sa.String(128), nullable=False),
        sa.Column("registry_snapshot_version", sa.Integer(), nullable=False),
        sa.Column("reason", sa.JSON(), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("assignments")
