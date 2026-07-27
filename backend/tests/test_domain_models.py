from datetime import UTC, datetime, timedelta

from app.domain.models import (
    Artifact,
    CapabilityRecord,
    DagSnapshot,
    Lease,
    Run,
    TaskAttempt,
    TaskNode,
    WorkerRecord,
)


def test_run_and_dag_snapshot_are_json_serializable() -> None:
    run = Run(
        run_id="run_01",
        tenant_id="tenant_01",
        request_id="trace_01",
        goal="Analyze product reviews",
    )
    snapshot = DagSnapshot(
        dag_id="dag_01",
        run_id=run.run_id,
        version=1,
        definition={"nodes": []},
    )

    assert run.model_dump(mode="json")["protocol_version"] == "v1"
    assert snapshot.model_dump(mode="json")["run_id"] == "run_01"


def test_task_attempt_and_artifact_keep_traceable_links() -> None:
    task = TaskNode(
        task_id="task_01",
        run_id="run_01",
        dag_version=1,
        type="map",
        objective="Extract review findings",
        output_contract="review_findings.v1",
        timeout_ms=1_000,
    )
    attempt = TaskAttempt(
        attempt_id="attempt_01",
        assignment_id="assignment_01",
        run_id=task.run_id,
        task_id=task.task_id,
        worker_id="worker_01",
        ordinal=1,
        idempotency_key="key_01",
    )
    artifact = Artifact(
        artifact_id="artifact_01",
        run_id=task.run_id,
        task_id=task.task_id,
        attempt_id=attempt.attempt_id,
        kind="task_result",
        contract=task.output_contract,
        content_hash="sha256:abc",
    )

    assert artifact.model_dump(mode="json")["attempt_id"] == "attempt_01"


def test_worker_capability_and_lease_are_json_serializable() -> None:
    capability = CapabilityRecord(
        name="information_extraction",
        version="v1",
        input_schema="document_chunk.v1",
        output_schema="review_findings.v1",
    )
    worker = WorkerRecord(
        worker_id="worker_01",
        role="worker",
        display_name="Mock Worker 01",
        endpoints=({"protocol": "http", "url": "https://worker.example/v1/tasks"},),
        capabilities=(capability,),
        resources={"max_concurrency": 1},
        failure_domain="host:worker-01",
    )
    now = datetime.now(UTC)
    lease = Lease(
        lease_id="lease_01",
        worker_id=worker.worker_id,
        sequence=1,
        issued_at=now,
        expires_at=now + timedelta(seconds=30),
        last_seen_at=now,
    )

    assert worker.model_dump(mode="json")["capabilities"][0]["name"] == "information_extraction"
    assert lease.model_dump(mode="json")["worker_id"] == worker.worker_id
