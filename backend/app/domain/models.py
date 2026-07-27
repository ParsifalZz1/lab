from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class DomainModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    protocol_version: Literal["v1"] = "v1"


class Run(DomainModel):
    run_id: str
    tenant_id: str
    request_id: str
    idempotency_key: str | None = None
    goal: str
    input_ref: str | None = None
    output_constraints: dict[str, Any] = Field(default_factory=dict)
    status: str = "RECEIVED"
    dag_version: int | None = None
    degraded: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    failure_code: str | None = None


class DagSnapshot(DomainModel):
    dag_id: str
    run_id: str
    version: int = Field(ge=1)
    definition: dict[str, Any]
    validation_summary: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class TaskNode(DomainModel):
    task_id: str
    run_id: str
    dag_version: int = Field(ge=1)
    type: str
    objective: str
    depends_on: tuple[str, ...] = ()
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_contract: str
    required_capabilities: tuple[dict[str, str], ...] = ()
    status: str = "PENDING"
    optional: bool = False
    priority: int = 50
    retry_policy: dict[str, Any] = Field(default_factory=dict)
    timeout_ms: int = Field(gt=0)
    ready_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    winner_attempt_id: str | None = None


class TaskAttempt(DomainModel):
    attempt_id: str
    assignment_id: str
    run_id: str
    task_id: str
    worker_id: str
    ordinal: int = Field(ge=1)
    idempotency_key: str
    status: str = "CREATED"
    dispatched_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    error_code: str | None = None
    error_message: str | None = None
    result_artifact_id: str | None = None


class Artifact(DomainModel):
    artifact_id: str
    run_id: str
    kind: str
    contract: str
    task_id: str | None = None
    attempt_id: str | None = None
    content: dict[str, Any] | None = None
    object_ref: str | None = None
    content_hash: str
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
