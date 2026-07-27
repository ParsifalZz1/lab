from fastapi.testclient import TestClient

from app.adapters.database import Base, create_database_engine
from app.config import Settings
from app.main import create_app
from app.repositories.events import EventOutbox


def test_create_get_and_cancel_run(tmp_path) -> None:
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'runs.db'}")
    Base.metadata.create_all(create_database_engine(settings))
    client = TestClient(create_app(settings))

    created = client.post("/v1/runs", json={"goal": "Analyze reviews", "input": {"comments": []}})
    run_id = created.json()["run_id"]

    assert created.status_code == 202
    assert client.get(f"/v1/runs/{run_id}").json()["status"] == "RECEIVED"
    assert client.post(f"/v1/runs/{run_id}/cancel").json()["status"] == "CANCELLED"


def test_event_stream_replays_events_after_cursor(tmp_path) -> None:
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'events.db'}")
    Base.metadata.create_all(create_database_engine(settings))
    app = create_app(settings)
    with app.state.session_factory.begin() as session:
        EventOutbox(session).append(
            topic="run.created",
            aggregate_type="run",
            aggregate_id="run_01",
            run_id="run_01",
            trace_id="trace",
            payload={"status": "RECEIVED"},
        )

    response = TestClient(app).get("/v1/runs/run_01/events", headers={"Last-Event-ID": "0"})

    assert "event: run.created" in response.text


def test_create_run_is_idempotent(tmp_path) -> None:
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'idempotency.db'}")
    Base.metadata.create_all(create_database_engine(settings))
    client = TestClient(create_app(settings))
    headers = {"Idempotency-Key": "request-01"}

    first = client.post("/v1/runs", headers=headers, json={"goal": "Analyze reviews", "input": {}})
    second = client.post("/v1/runs", headers=headers, json={"goal": "Analyze reviews", "input": {}})

    assert first.json()["run_id"] == second.json()["run_id"]
