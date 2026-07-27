from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.adapters.database import Base
from app.domain.events import DomainEvent
from app.domain.ids import new_id


class DomainEventRecord(Base):
    __tablename__ = "domain_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    topic: Mapped[str] = mapped_column(String(128), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(64), nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(64))
    worker_id: Mapped[str | None] = mapped_column(String(128))
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EventOutbox:
    def __init__(self, session: Session) -> None:
        self._session = session

    def append(
        self,
        *,
        topic: str,
        aggregate_type: str,
        aggregate_id: str,
        run_id: str,
        trace_id: str,
        payload: dict[str, Any],
        task_id: str | None = None,
        worker_id: str | None = None,
    ) -> DomainEvent:
        sequence = (
            self._session.scalar(
                select(func.coalesce(func.max(DomainEventRecord.sequence), 0)).where(
                    DomainEventRecord.run_id == run_id
                )
            )
            or 0
        ) + 1
        event = DomainEvent(
            event_id=new_id("event"),
            sequence=sequence,
            topic=topic,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            run_id=run_id,
            task_id=task_id,
            worker_id=worker_id,
            trace_id=trace_id,
            payload=payload,
        )
        self._session.add(DomainEventRecord(**event.model_dump(exclude={"protocol_version"})))
        return event
