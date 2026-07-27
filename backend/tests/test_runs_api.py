from fastapi.testclient import TestClient

from app.adapters.database import Base, create_database_engine
from app.config import Settings
from app.main import create_app


def test_create_get_and_cancel_run(tmp_path) -> None:
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'runs.db'}")
    Base.metadata.create_all(create_database_engine(settings))
    client = TestClient(create_app(settings))

    created = client.post("/v1/runs", json={"goal": "Analyze reviews", "input": {"comments": []}})
    run_id = created.json()["run_id"]

    assert created.status_code == 202
    assert client.get(f"/v1/runs/{run_id}").json()["status"] == "RECEIVED"
    assert client.post(f"/v1/runs/{run_id}/cancel").json()["status"] == "CANCELLED"
