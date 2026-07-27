from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.adapters.database import Base
from app.domain.dag import DagCapability, DagDefinition, DagNode
from app.repositories.records import RunRecord, TaskNodeRecord
from app.repositories.task_nodes import TaskNodeRepository


def test_task_nodes_are_created_only_after_valid_dag_check() -> None:
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
            status="RECEIVED",
            degraded=False,
            created_at=now,
            updated_at=now,
        )
    )
    dag = DagDefinition(
        dag_id="dag",
        version=1,
        nodes=(
            DagNode(
                node_id="extract",
                type="map",
                objective="Extract",
                output_contract="findings.v1",
                required_capabilities=(DagCapability(name="extract", version="v1"),),
                timeout_ms=1_000,
            ),
        ),
    )

    TaskNodeRepository(session).create_from_dag("run_01", dag)
    session.commit()

    assert session.scalars(select(TaskNodeRecord)).one().task_id == "extract"
