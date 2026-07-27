from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.adapters.database import Base
from app.config import Settings
from app.domain.models import CapabilityRecord, WorkerRecord
from app.domain.states import WorkerStatus
from app.repositories.events import DomainEventRecord
from app.repositories.records import WorkerRecordDb
from app.services.registry import RegistryService


def test_registering_the_same_worker_updates_its_record() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    service = RegistryService(session, Settings(_env_file=None))
    worker = WorkerRecord(
        worker_id="worker_01",
        role="worker",
        display_name="Worker 01",
        endpoints=({"protocol": "https", "url": "https://worker.example/tasks"},),
        capabilities=(
            CapabilityRecord(
                name="information_extraction",
                version="v1",
                input_schema="input.v1",
                output_schema="output.v1",
            ),
        ),
        resources={"max_concurrency": 1},
        failure_domain="host:01",
    )

    service.register(worker)
    service.register(worker)
    session.commit()

    assert len(service.get_ready_workers()) == 1
    assert session.query(DomainEventRecord).count() == 1


def test_lease_scan_marks_worker_suspect_then_offline() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    settings = Settings(_env_file=None, registry_heartbeat_seconds=10, registry_lease_seconds=30)
    service = RegistryService(session, settings)
    worker = WorkerRecord(
        worker_id="worker_01",
        role="worker",
        display_name="Worker 01",
        endpoints=({"protocol": "https", "url": "https://worker.example/tasks"},),
        capabilities=(
            CapabilityRecord(
                name="extract", version="v1", input_schema="in.v1", output_schema="out.v1"
            ),
        ),
        resources={"max_concurrency": 1},
        failure_domain="host:01",
    )
    started_at = datetime.now(UTC)
    service.register(worker, now=started_at)
    session.flush()

    service.scan_expired_leases(started_at + timedelta(seconds=11))
    assert service.get_ready_workers() == []
    service.scan_expired_leases(started_at + timedelta(seconds=31))
    assert session.get(WorkerRecordDb, worker.worker_id).status == WorkerStatus.OFFLINE.value


def test_candidates_filter_by_capability_and_region() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    service = RegistryService(session, Settings(_env_file=None))
    worker = WorkerRecord(
        worker_id="worker_01",
        role="worker",
        display_name="Worker 01",
        endpoints=({"protocol": "https", "url": "https://worker.example/tasks"},),
        capabilities=(
            CapabilityRecord(
                name="extract", version="v1", input_schema="in.v1", output_schema="out.v1"
            ),
        ),
        resources={"max_concurrency": 1},
        location={"region": "cn-shanghai"},
        failure_domain="host:01",
    )
    service.register(worker)
    session.flush()

    candidates = service.find_candidates(
        capability_name="extract", capability_version="v1", region="cn-shanghai"
    )

    assert [candidate.worker_id for candidate in candidates] == ["worker_01"]
