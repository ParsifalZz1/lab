import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.registry import get_session
from app.domain.ids import new_run_id
from app.repositories.events import DomainEventRecord
from app.repositories.records import DagSnapshotRecord, RunRecord, TaskNodeRecord
from app.services.run_lifecycle import cancel_run

router = APIRouter(prefix="/v1/runs", tags=["runs"])


class CreateRunRequest(BaseModel):
    goal: str = Field(min_length=1)
    input: dict[str, Any] | None = None
    output: dict[str, Any] = Field(default_factory=dict)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def create_run(
    body: CreateRunRequest, request: Request, session: Session = Depends(get_session)
) -> dict[str, object]:
    if body.input is None:
        raise HTTPException(status_code=400, detail="input is required")
    now = datetime.now(UTC)
    run = RunRecord(
        run_id=new_run_id(),
        tenant_id="local",
        request_id=request.headers.get("X-Request-Id", "local"),
        goal=body.goal,
        input_ref=None,
        output_constraints=body.output,
        status="RECEIVED",
        degraded=False,
        created_at=now,
        updated_at=now,
    )
    session.add(run)
    return {"run_id": run.run_id, "status": run.status, "created_at": run.created_at}


@router.get("/{run_id}")
def get_run(run_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    run = session.get(RunRecord, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "run_id": run.run_id,
        "status": run.status,
        "dag_version": run.dag_version,
        "degraded": run.degraded,
    }


@router.post("/{run_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
def cancel_run_endpoint(run_id: str, session: Session = Depends(get_session)) -> dict[str, str]:
    try:
        run = cancel_run(session, run_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {"run_id": run.run_id, "status": run.status}


@router.get("/{run_id}/dag")
def get_dag(run_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    snapshot = session.scalars(
        select(DagSnapshotRecord)
        .where(DagSnapshotRecord.run_id == run_id)
        .order_by(DagSnapshotRecord.version.desc())
    ).first()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="DAG not found")
    return {
        "dag_id": snapshot.dag_id,
        "version": snapshot.version,
        "definition": snapshot.definition,
    }


@router.get("/{run_id}/tasks")
def list_tasks(run_id: str, session: Session = Depends(get_session)) -> list[dict[str, object]]:
    return [
        {"task_id": task.task_id, "status": task.status, "depends_on": task.depends_on}
        for task in session.scalars(select(TaskNodeRecord).where(TaskNodeRecord.run_id == run_id))
    ]


@router.get("/{run_id}/events")
def stream_events(
    run_id: str,
    request: Request,
    session: Session = Depends(get_session),
) -> StreamingResponse:
    last_event_id = int(request.headers.get("Last-Event-ID", "0"))
    events = session.scalars(
        select(DomainEventRecord)
        .where(DomainEventRecord.run_id == run_id, DomainEventRecord.sequence > last_event_id)
        .order_by(DomainEventRecord.sequence)
    ).all()

    def body():
        for event in events:
            yield (
                f"id: {event.sequence}\nevent: {event.topic}\n"
                f"data: {json.dumps(event.payload)}\n\n"
            )

    return StreamingResponse(body(), media_type="text/event-stream")
