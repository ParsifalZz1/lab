import asyncio
from datetime import UTC, datetime, timedelta

import httpx

from app.adapters.worker_http import WorkerHttpAdapter
from app.domain.execution import ExecutionOptions, TaskEnvelope


def test_http_adapter_parses_matching_worker_result() -> None:
    async def run_test() -> str:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "protocol_version": "v1",
                    "run_id": "run",
                    "task_id": "task",
                    "attempt_id": "attempt",
                    "trace_id": "trace",
                    "worker_id": "worker",
                    "status": "SUCCEEDED",
                    "result": {"findings": []},
                },
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            envelope = TaskEnvelope(
                run_id="run",
                task_id="task",
                attempt_id="attempt",
                assignment_id="assignment",
                trace_id="trace",
                idempotency_key="key",
                capability={"name": "extract", "version": "v1"},
                objective="Extract",
                input={},
                output_contract="findings.v1",
                execution=ExecutionOptions(
                    max_output_tokens=10,
                    deadline_at=datetime.now(UTC) + timedelta(seconds=1),
                    attempt=1,
                ),
            )
            return (
                await WorkerHttpAdapter(client).execute("https://worker.example/tasks", envelope)
            ).status

    assert asyncio.run(run_test()) == "SUCCEEDED"
