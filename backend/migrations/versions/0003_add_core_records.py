"""Add core persistence records and query indexes.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("run_id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128)),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("input_ref", sa.String(512)),
        sa.Column("output_constraints", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("dag_version", sa.Integer()),
        sa.Column("degraded", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("failure_code", sa.String(128)),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_runs_tenant_idempotency"),
    )
    op.create_index("ix_runs_status_updated_at", "runs", ["status", "updated_at"])
    op.create_table(
        "dag_snapshots",
        sa.Column("dag_id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.run_id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("validation_summary", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "task_nodes",
        sa.Column("task_id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.run_id"), nullable=False),
        sa.Column("dag_version", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("depends_on", sa.JSON(), nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=False),
        sa.Column("output_contract", sa.String(128), nullable=False),
        sa.Column("required_capabilities", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("optional", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("retry_policy", sa.JSON(), nullable=False),
        sa.Column("timeout_ms", sa.Integer(), nullable=False),
        sa.Column("ready_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("winner_attempt_id", sa.String(64)),
    )
    op.create_index(
        "ix_task_nodes_run_status_priority", "task_nodes", ["run_id", "status", "priority"]
    )
    op.create_table(
        "task_attempts",
        sa.Column("attempt_id", sa.String(64), primary_key=True),
        sa.Column("assignment_id", sa.String(64), nullable=False),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.run_id"), nullable=False),
        sa.Column("task_id", sa.String(64), sa.ForeignKey("task_nodes.task_id"), nullable=False),
        sa.Column("worker_id", sa.String(128), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("error_code", sa.String(128)),
        sa.Column("error_message", sa.Text()),
        sa.Column("result_artifact_id", sa.String(64)),
        sa.UniqueConstraint("task_id", "ordinal", name="uq_task_attempts_task_ordinal"),
    )
    op.create_table(
        "artifacts",
        sa.Column("artifact_id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.run_id"), nullable=False),
        sa.Column("task_id", sa.String(64)),
        sa.Column("attempt_id", sa.String(64)),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("contract", sa.String(128), nullable=False),
        sa.Column("content", sa.JSON()),
        sa.Column("object_ref", sa.String(512)),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("source_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "worker_records",
        sa.Column("worker_id", sa.String(128), primary_key=True),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("endpoints", sa.JSON(), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("resources", sa.JSON(), nullable=False),
        sa.Column("location", sa.JSON(), nullable=False),
        sa.Column("failure_domain", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_worker_records_status", "worker_records", ["status"])
    op.create_table(
        "leases",
        sa.Column("lease_id", sa.String(64), primary_key=True),
        sa.Column(
            "worker_id", sa.String(128), sa.ForeignKey("worker_records.worker_id"), nullable=False
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_leases_expires_at", "leases", ["expires_at"])


def downgrade() -> None:
    op.drop_table("leases")
    op.drop_table("worker_records")
    op.drop_table("artifacts")
    op.drop_table("task_attempts")
    op.drop_table("task_nodes")
    op.drop_table("dag_snapshots")
    op.drop_table("runs")
