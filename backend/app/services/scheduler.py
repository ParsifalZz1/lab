from app.repositories.records import WorkerRecordDb


class NoEligibleWorkerError(LookupError):
    pass


def choose_least_loaded_worker(candidates: list[WorkerRecordDb]) -> WorkerRecordDb:
    if not candidates:
        raise NoEligibleWorkerError("No eligible Worker is available")
    return min(
        candidates,
        key=lambda worker: (
            worker.active_tasks / worker.resources["max_concurrency"],
            worker.worker_id,
        ),
    )
