from uuid import UUID

from app.domain.ids import new_attempt_id, new_dag_id, new_run_id, new_task_id


def fixed_uuid() -> UUID:
    return UUID("12345678-1234-5678-1234-567812345678")


def test_domain_ids_have_stable_prefixes_and_opaque_values() -> None:
    assert new_run_id(fixed_uuid) == "run_12345678123456781234567812345678"
    assert new_dag_id(fixed_uuid) == "dag_12345678123456781234567812345678"
    assert new_task_id(fixed_uuid) == "task_12345678123456781234567812345678"
    assert new_attempt_id(fixed_uuid) == "attempt_12345678123456781234567812345678"


def test_generated_ids_do_not_repeat() -> None:
    assert new_run_id() != new_run_id()
