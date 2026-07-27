from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.states import AttemptStatus, RunStatus, TaskStatus, WorkerStatus


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
    status: RunStatus = RunStatus.RECEIVED
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
    status: TaskStatus = TaskStatus.PENDING
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
    status: AttemptStatus = AttemptStatus.CREATED
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


class CapabilityRecord(DomainModel):
    name: str
    version: str = Field(pattern=r"^v[1-9][0-9]*$")
    input_schema: str
    output_schema: str
    constraints: dict[str, Any] = Field(default_factory=dict)
    quality_hints: dict[str, Any] = Field(default_factory=dict)


class Endpoint(DomainModel):
    protocol: Literal["http", "https"]
    url: str = Field(pattern=r"^https?://")


class WorkerResources(DomainModel):
    max_concurrency: int = Field(gt=0)
    context_window: int | None = Field(default=None, gt=0)


class WorkerRecord(DomainModel):
    worker_id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]{2,127}$")
    role: str
    display_name: str
    endpoints: tuple[Endpoint, ...] = Field(min_length=1)
    capabilities: tuple[CapabilityRecord, ...]
    resources: WorkerResources
    location: dict[str, str] = Field(default_factory=dict)
    failure_domain: str
    status: WorkerStatus = WorkerStatus.REGISTERING
    version: int = Field(default=1, ge=1)
    updated_at: datetime = Field(default_factory=utc_now)


class Lease(DomainModel):
    lease_id: str
    worker_id: str
    sequence: int = Field(ge=0)
    issued_at: datetime
    expires_at: datetime
    last_seen_at: datetime
