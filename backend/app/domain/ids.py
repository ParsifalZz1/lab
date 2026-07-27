from collections.abc import Callable
from uuid import UUID, uuid4

IdFactory = Callable[[], UUID]


def new_id(prefix: str, factory: IdFactory = uuid4) -> str:
    return f"{prefix}_{factory().hex}"


def new_run_id(factory: IdFactory = uuid4) -> str:
    return new_id("run", factory)


def new_dag_id(factory: IdFactory = uuid4) -> str:
    return new_id("dag", factory)


def new_task_id(factory: IdFactory = uuid4) -> str:
    return new_id("task", factory)


def new_attempt_id(factory: IdFactory = uuid4) -> str:
    return new_id("attempt", factory)
