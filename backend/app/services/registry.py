from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.domain.ids import new_id
from app.domain.models import WorkerRecord
from app.domain.states import WorkerStatus
from app.repositories.records import LeaseRecord, WorkerRecordDb


class RegistryService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    def register(self, worker: WorkerRecord, now: datetime | None = None) -> LeaseRecord:
        now = now or datetime.now(UTC)
        record = self._session.get(WorkerRecordDb, worker.worker_id)
        values = {
            "role": worker.role,
            "display_name": worker.display_name,
            "endpoints": [endpoint.model_dump() for endpoint in worker.endpoints],
            "capabilities": [capability.model_dump() for capability in worker.capabilities],
            "resources": worker.resources.model_dump(),
            "location": worker.location,
            "failure_domain": worker.failure_domain,
            "status": WorkerStatus.READY.value,
            "version": (record.version + 1) if record else 1,
            "updated_at": now,
        }
        if record is None:
            record = WorkerRecordDb(worker_id=worker.worker_id, **values)
            self._session.add(record)
        else:
            for key, value in values.items():
                setattr(record, key, value)
        lease = LeaseRecord(
            lease_id=new_id("lease"),
            worker_id=worker.worker_id,
            sequence=0,
            issued_at=now,
            expires_at=now + timedelta(seconds=self._settings.registry_lease_seconds),
            last_seen_at=now,
        )
        self._session.add(lease)
        return lease

    def heartbeat(self, worker_id: str, lease_id: str, sequence: int) -> LeaseRecord:
        lease = self._session.get(LeaseRecord, lease_id)
        if lease is None or lease.worker_id != worker_id or sequence <= lease.sequence:
            raise ValueError("Invalid or out-of-order worker heartbeat")
        now = datetime.now(UTC)
        lease.sequence = sequence
        lease.last_seen_at = now
        lease.expires_at = now + timedelta(seconds=self._settings.registry_lease_seconds)
        return lease

    def get_ready_workers(self) -> list[WorkerRecordDb]:
        return list(
            self._session.scalars(
                select(WorkerRecordDb).where(WorkerRecordDb.status.in_(["READY", "BUSY"]))
            )
        )
