from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.domain.dag import DagDefinition
from app.domain.ids import new_dag_id
from app.repositories.records import DagSnapshotRecord
from app.services.dag_validator import DagValidationIssue, validate_dag


class DagSnapshotRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, run_id: str, dag: DagDefinition) -> DagSnapshotRecord:
        issues = validate_dag(dag)
        snapshot = DagSnapshotRecord(
            dag_id=new_dag_id(),
            run_id=run_id,
            version=dag.version,
            definition=dag.model_dump(mode="json"),
            validation_summary={
                "valid": not issues,
                "issues": [issue.model_dump() for issue in issues],
            },
            created_at=datetime.now(UTC),
        )
        self._session.add(snapshot)
        return snapshot

    def get_issues(self, snapshot: DagSnapshotRecord) -> list[DagValidationIssue]:
        return [
            DagValidationIssue.model_validate(issue)
            for issue in snapshot.validation_summary["issues"]
        ]
