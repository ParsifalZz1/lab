from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.states import TaskStatus
from app.repositories.records import RunRecord, TaskNodeRecord


def cancel_run(session: Session, run_id: str) -> RunRecord:
    run = session.get(RunRecord, run_id)
    if run is None:
        raise LookupError(f"Run not found: {run_id}")
    tasks = session.scalars(select(TaskNodeRecord).where(TaskNodeRecord.run_id == run_id)).all()
    for task in tasks:
        if task.status in {
            TaskStatus.PENDING.value,
            TaskStatus.READY.value,
            TaskStatus.SCHEDULED.value,
        }:
            task.status = TaskStatus.CANCELLED.value
            task.finished_at = datetime.now(UTC)
    run.status = "CANCELLED"
    run.completed_at = datetime.now(UTC)
    run.updated_at = run.completed_at
    return run
