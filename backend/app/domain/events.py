from datetime import UTC, datetime
from typing import Any

from pydantic import Field

from app.domain.models import DomainModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class DomainEvent(DomainModel):
    event_id: str
    sequence: int = Field(ge=1)
    topic: str
    aggregate_type: str
    aggregate_id: str
    run_id: str
    trace_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    task_id: str | None = None
    worker_id: str | None = None
    occurred_at: datetime = Field(default_factory=utc_now)
    published_at: datetime | None = None
