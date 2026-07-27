from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.adapters.database import Base
from app.config import Settings
from app.domain.models import CapabilityRecord, WorkerRecord
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
