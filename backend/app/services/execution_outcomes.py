from enum import StrEnum

from app.domain.results import TaskResult


class ExecutionOutcome(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    RETRY = "RETRY"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


def classify_result(result: TaskResult) -> ExecutionOutcome:
    if result.status == "SUCCEEDED":
        return ExecutionOutcome.SUCCEEDED
    if result.status == "REJECTED_OVERLOADED":
        return ExecutionOutcome.REJECTED
    if result.status == "TIMED_OUT" or (result.error and result.error.retryable):
        return ExecutionOutcome.RETRY
    return ExecutionOutcome.FAILED
