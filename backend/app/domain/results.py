from datetime import datetime
from typing import Any

from pydantic import Field

from app.domain.models import DomainModel


class TaskError(DomainModel):
    code: str
    message: str
    retryable: bool


class TaskResult(DomainModel):
    run_id: str
    task_id: str
    attempt_id: str
    trace_id: str
    worker_id: str
    status: str
    output_contract: str | None = None
    result: dict[str, Any] | None = None
    error: TaskError | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    latency_ms: int | None = Field(default=None, ge=0)
