from collections.abc import Mapping
from enum import StrEnum


class RunStatus(StrEnum):
    RECEIVED = "RECEIVED"
    PLANNING = "PLANNING"
    VALIDATING = "VALIDATING"
    SCHEDULING = "SCHEDULING"
    EXECUTING = "EXECUTING"
    REDUCING = "REDUCING"
    SUCCEEDED = "SUCCEEDED"
    PARTIALLY_SUCCEEDED = "PARTIALLY_SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    READY = "READY"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class AttemptStatus(StrEnum):
    CREATED = "CREATED"
    DISPATCHED = "DISPATCHED"
    ACCEPTED = "ACCEPTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    REPORTED = "REPORTED"


class WorkerStatus(StrEnum):
    REGISTERING = "REGISTERING"
    READY = "READY"
    BUSY = "BUSY"
    DRAINING = "DRAINING"
    SUSPECT = "SUSPECT"
    OFFLINE = "OFFLINE"


class InvalidStateTransition(ValueError):
    pass


RUN_TRANSITIONS: Mapping[RunStatus, frozenset[RunStatus]] = {
    RunStatus.RECEIVED: frozenset({RunStatus.PLANNING, RunStatus.CANCELLED, RunStatus.FAILED}),
    RunStatus.PLANNING: frozenset({RunStatus.VALIDATING, RunStatus.CANCELLED, RunStatus.FAILED}),
    RunStatus.VALIDATING: frozenset({RunStatus.SCHEDULING, RunStatus.CANCELLED, RunStatus.FAILED}),
    RunStatus.SCHEDULING: frozenset({RunStatus.EXECUTING, RunStatus.CANCELLED, RunStatus.FAILED}),
    RunStatus.EXECUTING: frozenset(
        {RunStatus.SCHEDULING, RunStatus.REDUCING, RunStatus.CANCELLED, RunStatus.FAILED}
    ),
    RunStatus.REDUCING: frozenset(
        {RunStatus.SUCCEEDED, RunStatus.PARTIALLY_SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELLED}
    ),
}

TASK_TRANSITIONS: Mapping[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PENDING: frozenset({TaskStatus.READY, TaskStatus.BLOCKED, TaskStatus.CANCELLED}),
    TaskStatus.READY: frozenset({TaskStatus.SCHEDULED, TaskStatus.CANCELLED}),
    TaskStatus.SCHEDULED: frozenset({TaskStatus.RUNNING, TaskStatus.PENDING, TaskStatus.CANCELLED}),
    TaskStatus.RUNNING: frozenset(
        {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.PENDING, TaskStatus.CANCELLED}
    ),
}

ATTEMPT_TRANSITIONS: Mapping[AttemptStatus, frozenset[AttemptStatus]] = {
    AttemptStatus.CREATED: frozenset({AttemptStatus.DISPATCHED, AttemptStatus.CANCELLED}),
    AttemptStatus.DISPATCHED: frozenset(
        {
            AttemptStatus.ACCEPTED,
            AttemptStatus.REJECTED,
            AttemptStatus.TIMED_OUT,
            AttemptStatus.CANCELLED,
        }
    ),
    AttemptStatus.ACCEPTED: frozenset(
        {AttemptStatus.RUNNING, AttemptStatus.TIMED_OUT, AttemptStatus.CANCELLED}
    ),
    AttemptStatus.RUNNING: frozenset(
        {
            AttemptStatus.SUCCEEDED,
            AttemptStatus.FAILED,
            AttemptStatus.TIMED_OUT,
            AttemptStatus.CANCELLED,
        }
    ),
    AttemptStatus.SUCCEEDED: frozenset({AttemptStatus.REPORTED}),
    AttemptStatus.FAILED: frozenset({AttemptStatus.REPORTED}),
    AttemptStatus.TIMED_OUT: frozenset({AttemptStatus.REPORTED}),
    AttemptStatus.CANCELLED: frozenset({AttemptStatus.REPORTED}),
    AttemptStatus.REJECTED: frozenset({AttemptStatus.REPORTED}),
}

WORKER_TRANSITIONS: Mapping[WorkerStatus, frozenset[WorkerStatus]] = {
    WorkerStatus.REGISTERING: frozenset({WorkerStatus.READY, WorkerStatus.OFFLINE}),
    WorkerStatus.READY: frozenset(
        {WorkerStatus.BUSY, WorkerStatus.DRAINING, WorkerStatus.SUSPECT, WorkerStatus.OFFLINE}
    ),
    WorkerStatus.BUSY: frozenset(
        {WorkerStatus.READY, WorkerStatus.DRAINING, WorkerStatus.SUSPECT, WorkerStatus.OFFLINE}
    ),
    WorkerStatus.DRAINING: frozenset({WorkerStatus.READY, WorkerStatus.OFFLINE}),
    WorkerStatus.SUSPECT: frozenset({WorkerStatus.READY, WorkerStatus.OFFLINE}),
    WorkerStatus.OFFLINE: frozenset({WorkerStatus.REGISTERING}),
}


def ensure_transition(
    current: StrEnum, target: StrEnum, transitions: Mapping[StrEnum, frozenset[StrEnum]]
) -> None:
    if target not in transitions.get(current, frozenset()):
        raise InvalidStateTransition(f"Cannot transition from {current} to {target}")
