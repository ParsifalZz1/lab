"""Add the durable event outbox.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "domain_events",
        sa.Column("event_id", sa.String(length=64), primary_key=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64)),
        sa.Column("worker_id", sa.String(length=128)),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("run_id", "sequence", name="uq_domain_events_run_sequence"),
    )


def downgrade() -> None:
    op.drop_table("domain_events")
