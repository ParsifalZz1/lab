import pytest

from app.domain.states import (
    ATTEMPT_TRANSITIONS,
    RUN_TRANSITIONS,
    AttemptStatus,
    InvalidStateTransition,
    RunStatus,
    ensure_transition,
)


def test_valid_run_state_transition_is_accepted() -> None:
    ensure_transition(RunStatus.RECEIVED, RunStatus.PLANNING, RUN_TRANSITIONS)


def test_invalid_run_state_transition_is_rejected() -> None:
    with pytest.raises(InvalidStateTransition, match="RECEIVED to SUCCEEDED"):
        ensure_transition(RunStatus.RECEIVED, RunStatus.SUCCEEDED, RUN_TRANSITIONS)


def test_attempt_cannot_skip_dispatch() -> None:
    with pytest.raises(InvalidStateTransition):
        ensure_transition(AttemptStatus.CREATED, AttemptStatus.RUNNING, ATTEMPT_TRANSITIONS)
