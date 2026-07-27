from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.adapters.database import Base
from app.domain.dag import DagCapability, DagDefinition, DagNode
from app.repositories.dag_snapshots import DagSnapshotRepository
from app.repositories.records import RunRecord


def test_dag_snapshot_persists_definition_and_validation_summary() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    now = datetime.now(UTC)
    session.add(
        RunRecord(
            run_id="run_01",
            tenant_id="tenant_01",
            request_id="trace_01",
            goal="Analyze reviews",
            output_constraints={},
            status="RECEIVED",
            degraded=False,
            created_at=now,
            updated_at=now,
        )
    )
    dag = DagDefinition(
        dag_id="draft_01",
        version=1,
        nodes=(
            DagNode(
                node_id="extract",
                type="map",
                objective="Extract findings",
                output_contract="review_findings.v1",
                required_capabilities=(DagCapability(name="extract", version="v1"),),
                timeout_ms=1_000,
            ),
        ),
    )

    snapshot = DagSnapshotRepository(session).save("run_01", dag)
    session.commit()

    assert snapshot.validation_summary["valid"] is True
    assert snapshot.definition["nodes"][0]["node_id"] == "extract"
