import asyncio
from datetime import datetime
from typing import Any

from pydantic import Field

from app.domain.models import DomainModel


class ExecutionOptions(DomainModel):
    max_output_tokens: int = Field(gt=0)
    deadline_at: datetime
    attempt: int = Field(ge=1)
    priority: int = 50


class TaskEnvelope(DomainModel):
    run_id: str
    task_id: str
    attempt_id: str
    assignment_id: str
    trace_id: str
    idempotency_key: str = Field(min_length=1)
    capability: dict[str, str]
    objective: str
    input: dict[str, Any]
    output_contract: str
    execution: ExecutionOptions
    security: dict[str, str] = Field(default_factory=dict)


class CancellationToken:
    def __init__(self) -> None:
        self._event = asyncio.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    async def wait(self) -> None:
        await self._event.wait()
