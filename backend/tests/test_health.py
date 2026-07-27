from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check_reports_process_liveness() -> None:
    response = TestClient(create_app()).get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-Id"].startswith("trace_")


def test_health_check_preserves_client_request_id() -> None:
    response = TestClient(create_app()).get("/healthz", headers={"X-Request-Id": "trace_test"})

    assert response.headers["X-Request-Id"] == "trace_test"


def test_openapi_exposes_versioned_run_api() -> None:
    schema = TestClient(create_app()).get("/openapi.json").json()

    assert "/v1/runs" in schema["paths"]
