import asyncio

from app.services.executor import ExecutionCoordinator


def test_execution_coordinator_enforces_concurrency_limit() -> None:
    async def run_test() -> tuple[list[int], int]:
        active = 0
        peak = 0

        async def job() -> int:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0)
            active -= 1
            return 1

        return await ExecutionCoordinator(2).execute([job, job, job, job]), peak

    results, peak = asyncio.run(run_test())

    assert results == [1, 1, 1, 1]
    assert peak == 2
