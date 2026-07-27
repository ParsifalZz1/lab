import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.adapters.database import Base
from app.config import Settings
from app.services.registry import RegistryService
from app.services.scheduler import NoEligibleWorkerError, choose_least_loaded_worker
from app.workers.register_mock_workers import build_mock_workers


def test_scheduler_chooses_lowest_active_task_ratio() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    registry = RegistryService(session, Settings(_env_file=None))
    first_worker, second_worker = build_mock_workers(2)
    first_lease = registry.register(first_worker)
    registry.register(second_worker)
    session.flush()
    registry.heartbeat(first_worker.worker_id, first_lease.lease_id, 1, 1, 0)

    chosen = choose_least_loaded_worker(registry.find_candidates())

    assert chosen.worker_id == second_worker.worker_id


def test_scheduler_rejects_empty_candidates() -> None:
    with pytest.raises(NoEligibleWorkerError):
        choose_least_loaded_worker([])
