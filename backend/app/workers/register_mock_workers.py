from app.adapters.database import create_session_factory
from app.config import get_settings
from app.domain.models import CapabilityRecord, WorkerRecord
from app.services.registry import RegistryService


def build_mock_workers(count: int = 8) -> list[WorkerRecord]:
    capability = CapabilityRecord(
        name="information_extraction",
        version="v1",
        input_schema="review_batch.v1",
        output_schema="review_findings.v1",
    )
    return [
        WorkerRecord(
            worker_id=f"mock-worker-{index:02d}",
            role="worker",
            display_name=f"Mock Worker {index:02d}",
            endpoints=({"protocol": "http", "url": f"http://mock-worker-{index:02d}/v1/tasks"},),
            capabilities=(capability,),
            resources={"max_concurrency": 1, "context_window": 8192},
            location={"region": "local"},
            failure_domain=f"host:mock-{index:02d}",
        )
        for index in range(1, count + 1)
    ]


def main() -> None:
    settings = get_settings()
    session_factory = create_session_factory(settings)
    with session_factory.begin() as session:
        service = RegistryService(session, settings)
        for worker in build_mock_workers():
            service.register(worker)


if __name__ == "__main__":
    main()
