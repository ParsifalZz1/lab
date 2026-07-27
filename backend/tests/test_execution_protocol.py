import asyncio
from datetime import UTC, datetime, timedelta

from app.domain.execution import CancellationToken, ExecutionOptions, TaskEnvelope


def test_task_envelope_is_versioned_and_json_serializable() -> None:
    envelope = TaskEnvelope(
        run_id="run_01",
        task_id="task_01",
        attempt_id="attempt_01",
        assignment_id="assignment_01",
        trace_id="trace_01",
        idempotency_key="key_01",
        capability={"name": "extract", "version": "v1"},
        objective="Extract findings",
        input={"batch": 1},
        output_contract="findings.v1",
        execution=ExecutionOptions(
            max_output_tokens=100, deadline_at=datetime.now(UTC) + timedelta(seconds=1), attempt=1
        ),
    )

    assert envelope.model_dump(mode="json")["protocol_version"] == "v1"


def test_cancellation_token_signals_waiters() -> None:
    token = CancellationToken()
    token.cancel()
    asyncio.run(token.wait())

    assert token.cancelled
