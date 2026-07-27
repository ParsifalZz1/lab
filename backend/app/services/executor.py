import asyncio
from collections.abc import Awaitable, Callable, Iterable
from typing import TypeVar

Result = TypeVar("Result")


class ExecutionCoordinator:
    def __init__(self, max_concurrency: int) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def execute(self, jobs: Iterable[Callable[[], Awaitable[Result]]]) -> list[Result]:
        async def run(job: Callable[[], Awaitable[Result]]) -> Result:
            async with self._semaphore:
                return await job()

        return list(await asyncio.gather(*(run(job) for job in jobs)))
