"""Add Worker load counters.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("worker_records") as batch:
        batch.add_column(
            sa.Column("active_tasks", sa.Integer(), nullable=False, server_default="0")
        )
        batch.add_column(sa.Column("queue_depth", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("worker_records") as batch:
        batch.drop_column("queue_depth")
        batch.drop_column("active_tasks")
