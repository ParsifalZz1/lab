from app.domain.results import TaskError, TaskResult
from app.services.execution_outcomes import ExecutionOutcome, classify_result


def result(status: str, retryable: bool | None = None) -> TaskResult:
    return TaskResult(
        run_id="run",
        task_id="task",
        attempt_id="attempt",
        trace_id="trace",
        worker_id="worker",
        status=status,
        error=TaskError(code="error", message="failed", retryable=retryable)
        if retryable is not None
        else None,
    )


def test_execution_outcome_classifies_success_retry_failure_and_overload() -> None:
    assert classify_result(result("SUCCEEDED")) is ExecutionOutcome.SUCCEEDED
    assert classify_result(result("TIMED_OUT")) is ExecutionOutcome.RETRY
    assert classify_result(result("FAILED", retryable=True)) is ExecutionOutcome.RETRY
    assert classify_result(result("FAILED", retryable=False)) is ExecutionOutcome.FAILED
    assert classify_result(result("REJECTED_OVERLOADED")) is ExecutionOutcome.REJECTED
