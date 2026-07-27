from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.adapters.database import Base
from app.repositories.events import EventOutbox


def test_outbox_assigns_monotonic_sequences_per_run() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    outbox = EventOutbox(session)

    first = outbox.append(
        topic="run.created",
        aggregate_type="run",
        aggregate_id="run_01",
        run_id="run_01",
        trace_id="trace_01",
        payload={"status": "RECEIVED"},
    )
    second = outbox.append(
        topic="run.status_changed",
        aggregate_type="run",
        aggregate_id="run_01",
        run_id="run_01",
        trace_id="trace_01",
        payload={"from": "RECEIVED", "to": "PLANNING"},
    )
    session.commit()

    assert (first.sequence, second.sequence) == (1, 2)
