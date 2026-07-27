from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.domain.ids import new_id
from app.repositories.records import AssignmentRecord, WorkerRecordDb


class NoEligibleWorkerError(LookupError):
    pass


def choose_least_loaded_worker(candidates: list[WorkerRecordDb]) -> WorkerRecordDb:
    if not candidates:
        raise NoEligibleWorkerError("No eligible Worker is available")
    return min(
        candidates,
        key=lambda worker: (
            worker.active_tasks / worker.resources["max_concurrency"],
            worker.worker_id,
        ),
    )


def choose_retry_worker(
    candidates: list[WorkerRecordDb], previous_worker: WorkerRecordDb
) -> WorkerRecordDb:
    alternate_domain = [
        candidate
        for candidate in candidates
        if candidate.failure_domain != previous_worker.failure_domain
    ]
    return choose_least_loaded_worker(alternate_domain or candidates)


def create_assignment(
    session: Session,
    *,
    run_id: str,
    task_id: str,
    worker: WorkerRecordDb,
    registry_snapshot_version: int,
    timeout_ms: int,
) -> AssignmentRecord:
    now = datetime.now(UTC)
    assignment = AssignmentRecord(
        assignment_id=new_id("assignment"),
        run_id=run_id,
        task_id=task_id,
        worker_id=worker.worker_id,
        registry_snapshot_version=registry_snapshot_version,
        reason={"strategy": "least_active_tasks", "active_tasks": worker.active_tasks},
        deadline_at=now + timedelta(milliseconds=timeout_ms),
        created_at=now,
    )
    session.add(assignment)
    return assignment
