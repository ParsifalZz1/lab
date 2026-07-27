from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.domain.ids import new_id
from app.domain.models import WorkerRecord
from app.domain.states import WorkerStatus
from app.repositories.events import EventOutbox
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
            "active_tasks": 0,
            "queue_depth": 0,
            "updated_at": now,
        }
        if record is None:
            record = WorkerRecordDb(worker_id=worker.worker_id, **values)
            self._session.add(record)
            self._write_status_event(worker.worker_id, "REGISTERING", WorkerStatus.READY.value)
        else:
            for key, value in values.items():
                setattr(record, key, value)
            for previous_lease in self._session.scalars(
                select(LeaseRecord).where(LeaseRecord.worker_id == worker.worker_id)
            ):
                self._session.delete(previous_lease)
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

    def heartbeat(
        self, worker_id: str, lease_id: str, sequence: int, active_tasks: int, queue_depth: int
    ) -> LeaseRecord:
        lease = self._session.get(LeaseRecord, lease_id)
        if lease is None or lease.worker_id != worker_id or sequence <= lease.sequence:
            raise ValueError("Invalid or out-of-order worker heartbeat")
        now = datetime.now(UTC)
        lease.sequence = sequence
        lease.last_seen_at = now
        lease.expires_at = now + timedelta(seconds=self._settings.registry_lease_seconds)
        worker = self._session.get(WorkerRecordDb, worker_id)
        if worker is not None:
            worker.active_tasks = active_tasks
            worker.queue_depth = queue_depth
            next_status = WorkerStatus.BUSY.value if active_tasks else WorkerStatus.READY.value
            if worker.status != next_status:
                self._write_status_event(worker.worker_id, worker.status, next_status)
                worker.status = next_status
        return lease

    def get_ready_workers(self) -> list[WorkerRecordDb]:
        return list(
            self._session.scalars(
                select(WorkerRecordDb).where(WorkerRecordDb.status.in_(["READY", "BUSY"]))
            )
        )

    def find_candidates(
        self,
        *,
        role: str | None = None,
        capability_name: str | None = None,
        capability_version: str | None = None,
        region: str | None = None,
        min_context_window: int | None = None,
        status: str | None = None,
        now: datetime | None = None,
    ) -> list[WorkerRecordDb]:
        now = now or datetime.now(UTC)
        statement = select(WorkerRecordDb)
        if status:
            statement = statement.where(WorkerRecordDb.status == status)
        else:
            statement = statement.where(WorkerRecordDb.status.in_(["READY", "BUSY"]))
        workers = self._session.scalars(statement).all()
        candidates: list[WorkerRecordDb] = []
        for worker in workers:
            if role and worker.role != role:
                continue
            if region and worker.location.get("region") != region:
                continue
            if (
                min_context_window
                and worker.resources.get("context_window", 0) < min_context_window
            ):
                continue
            if worker.active_tasks >= worker.resources["max_concurrency"]:
                continue
            if capability_name and not any(
                capability.get("name") == capability_name
                and (capability_version is None or capability.get("version") == capability_version)
                for capability in worker.capabilities
            ):
                continue
            leases = self._session.scalars(
                select(LeaseRecord).where(LeaseRecord.worker_id == worker.worker_id)
            ).all()
            if not any(_as_utc(lease.expires_at) > now for lease in leases):
                continue
            candidates.append(worker)
        return candidates

    def scan_expired_leases(self, now: datetime | None = None) -> list[str]:
        now = now or datetime.now(UTC)
        changed_workers: list[str] = []
        leases = self._session.scalars(select(LeaseRecord)).all()
        for lease in leases:
            worker = self._session.get(WorkerRecordDb, lease.worker_id)
            if worker is None:
                continue
            expires_at = _as_utc(lease.expires_at)
            last_seen_at = _as_utc(lease.last_seen_at)
            if expires_at <= now:
                if worker.status != WorkerStatus.OFFLINE.value:
                    self._write_status_event(
                        worker.worker_id, worker.status, WorkerStatus.OFFLINE.value
                    )
                    worker.status = WorkerStatus.OFFLINE.value
                    changed_workers.append(worker.worker_id)
            elif last_seen_at + timedelta(
                seconds=self._settings.registry_heartbeat_seconds
            ) <= now and worker.status in {WorkerStatus.READY.value, WorkerStatus.BUSY.value}:
                self._write_status_event(
                    worker.worker_id, worker.status, WorkerStatus.SUSPECT.value
                )
                worker.status = WorkerStatus.SUSPECT.value
                changed_workers.append(worker.worker_id)
        return changed_workers

    def _write_status_event(self, worker_id: str, previous: str, current: str) -> None:
        EventOutbox(self._session).append(
            topic="worker.status_changed",
            aggregate_type="worker",
            aggregate_id=worker_id,
            run_id="registry",
            worker_id=worker_id,
            trace_id="registry",
            payload={"from": previous, "to": current},
        )


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
