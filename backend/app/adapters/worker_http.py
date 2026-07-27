import httpx

from app.domain.execution import TaskEnvelope
from app.domain.results import TaskResult


class WorkerHttpAdapter:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def execute(self, endpoint: str, envelope: TaskEnvelope) -> TaskResult:
        response = await self._client.post(endpoint, json=envelope.model_dump(mode="json"))
        response.raise_for_status()
        result = TaskResult.model_validate(response.json())
        if (result.run_id, result.task_id, result.attempt_id) != (
            envelope.run_id,
            envelope.task_id,
            envelope.attempt_id,
        ):
            raise ValueError("Worker result does not match task envelope")
        return result
