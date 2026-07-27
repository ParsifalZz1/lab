from sqlalchemy.orm import Session

from app.domain.dag import DagDefinition
from app.domain.states import TaskStatus
from app.repositories.records import TaskNodeRecord
from app.services.dag_validator import ensure_valid_dag


class TaskNodeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_from_dag(self, run_id: str, dag: DagDefinition) -> list[TaskNodeRecord]:
        ensure_valid_dag(dag)
        records = [
            TaskNodeRecord(
                task_id=node.node_id,
                run_id=run_id,
                dag_version=dag.version,
                type=node.type,
                objective=node.objective,
                depends_on=list(node.depends_on),
                input_data={
                    "inputs": [input_ref.model_dump(mode="json") for input_ref in node.inputs]
                },
                output_contract=node.output_contract,
                required_capabilities=[
                    capability.model_dump(mode="json") for capability in node.required_capabilities
                ],
                status=TaskStatus.PENDING.value,
                optional=node.optional,
                priority=node.priority,
                retry_policy=node.retry_policy.model_dump(mode="json"),
                timeout_ms=node.timeout_ms,
            )
            for node in dag.nodes
        ]
        self._session.add_all(records)
        return records
