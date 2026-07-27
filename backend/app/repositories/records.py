from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.database import Base


class RunRecord(Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    input_ref: Mapped[str | None] = mapped_column(String(512))
    output_constraints: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    dag_version: Mapped[int | None] = mapped_column(Integer)
    degraded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_code: Mapped[str | None] = mapped_column(String(128))


class DagSnapshotRecord(Base):
    __tablename__ = "dag_snapshots"

    dag_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.run_id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    definition: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    validation_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TaskNodeRecord(Base):
    __tablename__ = "task_nodes"

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.run_id"), nullable=False)
    dag_version: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    depends_on: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    input_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    output_contract: Mapped[str] = mapped_column(String(128), nullable=False)
    required_capabilities: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    retry_policy: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    winner_attempt_id: Mapped[str | None] = mapped_column(String(64))


class TaskAttemptRecord(Base):
    __tablename__ = "task_attempts"

    attempt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    assignment_id: Mapped[str] = mapped_column(String(64), nullable=False)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.run_id"), nullable=False)
    task_id: Mapped[str] = mapped_column(ForeignKey("task_nodes.task_id"), nullable=False)
    worker_id: Mapped[str] = mapped_column(String(128), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(128))
    error_message: Mapped[str | None] = mapped_column(Text)
    result_artifact_id: Mapped[str | None] = mapped_column(String(64))


class ArtifactRecord(Base):
    __tablename__ = "artifacts"

    artifact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.run_id"), nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(64))
    attempt_id: Mapped[str | None] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    contract: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    object_ref: Mapped[str | None] = mapped_column(String(512))
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkerRecordDb(Base):
    __tablename__ = "worker_records"

    worker_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    endpoints: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    capabilities: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    resources: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    location: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)
    failure_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LeaseRecord(Base):
    __tablename__ = "leases"

    lease_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    worker_id: Mapped[str] = mapped_column(ForeignKey("worker_records.worker_id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_runs_status_updated_at", RunRecord.status, RunRecord.updated_at)
Index(
    "ix_task_nodes_run_status_priority",
    TaskNodeRecord.run_id,
    TaskNodeRecord.status,
    TaskNodeRecord.priority,
)
Index(
    "ix_task_attempts_task_ordinal",
    TaskAttemptRecord.task_id,
    TaskAttemptRecord.ordinal,
    unique=True,
)
Index("ix_worker_records_status", WorkerRecordDb.status)
Index("ix_leases_expires_at", LeaseRecord.expires_at)
