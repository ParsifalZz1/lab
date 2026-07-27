from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.domain.models import WorkerRecord
from app.domain.states import WorkerStatus
from app.repositories.records import WorkerRecordDb
from app.services.registry import RegistryService

router = APIRouter(prefix="/v1/registry/nodes", tags=["registry"])


class HeartbeatRequest(BaseModel):
    lease_id: str
    sequence: int = Field(ge=1)


def get_session(request: Request) -> Generator[Session, None, None]:
    session = request.app.state.session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("", status_code=status.HTTP_201_CREATED)
def register_node(
    worker: WorkerRecord, request: Request, session: Session = Depends(get_session)
) -> dict[str, str]:
    lease = RegistryService(session, request.app.state.settings).register(worker)
    return {"worker_id": worker.worker_id, "lease_id": lease.lease_id, "status": "READY"}


@router.post("/{worker_id}/heartbeat")
def heartbeat(
    worker_id: str,
    body: HeartbeatRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> dict[str, str | int]:
    try:
        lease = RegistryService(session, request.app.state.settings).heartbeat(
            worker_id, body.lease_id, body.sequence
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"lease_id": lease.lease_id, "sequence": lease.sequence}


@router.post("/{worker_id}/drain")
def drain_node(worker_id: str, session: Session = Depends(get_session)) -> dict[str, str]:
    worker = session.get(WorkerRecordDb, worker_id)
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker not found")
    worker.status = WorkerStatus.DRAINING.value
    return {"worker_id": worker_id, "status": worker.status}


@router.delete("/{worker_id}")
def unregister_node(worker_id: str, session: Session = Depends(get_session)) -> dict[str, str]:
    worker = session.get(WorkerRecordDb, worker_id)
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker not found")
    worker.status = WorkerStatus.OFFLINE.value
    return {"worker_id": worker_id, "status": worker.status}
