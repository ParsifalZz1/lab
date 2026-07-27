from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.adapters.database import Base
from app.domain.states import TaskStatus
from app.repositories.records import RunRecord, TaskNodeRecord
from app.services.run_lifecycle import cancel_run
from app.services.task_progress import (
    mark_optional_task_failed,
    mark_task_succeeded,
    transition_task,
)


def task(task_id: str, depends_on: list[str]) -> TaskNodeRecord:
    return TaskNodeRecord(
        task_id=task_id,
        run_id="run_01",
        dag_version=1,
        type="map",
        objective="work",
        depends_on=depends_on,
        input_data={},
        output_contract="output.v1",
        required_capabilities=[],
        status="PENDING",
        optional=False,
        priority=50,
        retry_policy={},
        timeout_ms=1_000,
    )


def test_successful_dependencies_make_downstream_task_ready() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    now = datetime.now(UTC)
    session.add(
        RunRecord(
            run_id="run_01",
            tenant_id="tenant",
            request_id="trace",
            goal="goal",
            output_constraints={},
            status="EXECUTING",
            degraded=False,
            created_at=now,
            updated_at=now,
        )
    )
    first = task("first", [])
    second = task("second", [])
    downstream = task("reduce", ["first", "second"])
    session.add_all([first, second, downstream])
    session.flush()

    assert mark_task_succeeded(session, "first", "attempt_01") == []
    assert mark_task_succeeded(session, "second", "attempt_02") == ["reduce"]
    assert session.get(TaskNodeRecord, "reduce").status == "READY"


def test_task_state_machine_moves_through_execution_states() -> None:
    record = task("task", [])

    transition_task(record, TaskStatus.READY)
    transition_task(record, TaskStatus.SCHEDULED)
    transition_task(record, TaskStatus.RUNNING)
    transition_task(record, TaskStatus.SUCCEEDED)

    assert record.status == "SUCCEEDED"


def test_cancelling_run_cancels_unstarted_tasks() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    now = datetime.now(UTC)
    session.add(
        RunRecord(
            run_id="run_01",
            tenant_id="tenant",
            request_id="trace",
            goal="goal",
            output_constraints={},
            status="EXECUTING",
            degraded=False,
            created_at=now,
            updated_at=now,
        )
    )
    pending = task("pending", [])
    pending.run_id = "run_01"
    session.add(pending)
    session.flush()

    run = cancel_run(session, "run_01")

    assert run.status == "CANCELLED"
    assert session.get(TaskNodeRecord, "pending").status == "CANCELLED"


def test_optional_task_failure_keeps_missing_output_metadata() -> None:
    optional = task("optional", [])
    optional.optional = True

    mark_optional_task_failed(optional, "WORKER_OFFLINE")

    assert optional.status == "FAILED"
    assert optional.input_data["missing_output"]["error_code"] == "WORKER_OFFLINE"
