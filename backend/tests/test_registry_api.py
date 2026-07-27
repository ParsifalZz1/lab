from fastapi.testclient import TestClient

from app.adapters.database import Base, create_database_engine
from app.config import Settings
from app.main import create_app


def test_registry_registers_and_heartbeats_worker(tmp_path) -> None:
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'registry.db'}")
    Base.metadata.create_all(create_database_engine(settings))
    client = TestClient(create_app(settings))
    payload = {
        "worker_id": "worker_01",
        "role": "worker",
        "display_name": "Worker 01",
        "endpoints": [{"protocol": "https", "url": "https://worker.example/tasks"}],
        "capabilities": [
            {
                "name": "information_extraction",
                "version": "v1",
                "input_schema": "input.v1",
                "output_schema": "output.v1",
            }
        ],
        "resources": {"max_concurrency": 1},
        "failure_domain": "host:01",
    }

    registered = client.post("/v1/registry/nodes", json=payload)
    heartbeat = client.post(
        "/v1/registry/nodes/worker_01/heartbeat",
        json={"lease_id": registered.json()["lease_id"], "sequence": 1},
    )

    assert registered.status_code == 201
    assert heartbeat.json()["sequence"] == 1


def test_registry_rejects_invalid_endpoint_protocol(tmp_path) -> None:
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'registry.db'}")
    Base.metadata.create_all(create_database_engine(settings))
    response = TestClient(create_app(settings)).post(
        "/v1/registry/nodes",
        json={
            "worker_id": "worker_01",
            "role": "worker",
            "display_name": "Worker 01",
            "endpoints": [{"protocol": "ftp", "url": "ftp://worker.example/tasks"}],
            "capabilities": [
                {
                    "name": "information_extraction",
                    "version": "v1",
                    "input_schema": "input.v1",
                    "output_schema": "output.v1",
                }
            ],
            "resources": {"max_concurrency": 0},
            "failure_domain": "host:01",
        },
    )

    assert response.status_code == 422
