from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.states import TASK_TRANSITIONS, TaskStatus, ensure_transition
from app.repositories.records import TaskNodeRecord


def mark_task_succeeded(session: Session, task_id: str, attempt_id: str) -> list[str]:
    task = session.get(TaskNodeRecord, task_id)
    if task is None:
        raise LookupError(f"Task not found: {task_id}")
    task.status = TaskStatus.SUCCEEDED.value
    task.winner_attempt_id = attempt_id
    task.finished_at = datetime.now(UTC)
    newly_ready: list[str] = []
    children = session.scalars(
        select(TaskNodeRecord).where(
            TaskNodeRecord.run_id == task.run_id, TaskNodeRecord.status == "PENDING"
        )
    ).all()
    for child in children:
        if task_id not in child.depends_on:
            continue
        dependencies = session.scalars(
            select(TaskNodeRecord).where(TaskNodeRecord.task_id.in_(child.depends_on))
        ).all()
        if len(dependencies) == len(child.depends_on) and all(
            dependency.status == TaskStatus.SUCCEEDED.value for dependency in dependencies
        ):
            child.status = TaskStatus.READY.value
            child.ready_at = datetime.now(UTC)
            newly_ready.append(child.task_id)
    return newly_ready


def transition_task(task: TaskNodeRecord, target: TaskStatus) -> None:
    ensure_transition(TaskStatus(task.status), target, TASK_TRANSITIONS)
    task.status = target.value
