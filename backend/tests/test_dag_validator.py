from app.domain.dag import DagCapability, DagDefinition, DagNode, InputRef
from app.services.dag_validator import validate_dag


def node(node_id: str, **kwargs) -> DagNode:
    return DagNode(
        node_id=node_id,
        type="map",
        objective="Extract findings",
        output_contract="review_findings.v1",
        required_capabilities=(DagCapability(name="extract", version="v1"),),
        timeout_ms=1_000,
        **kwargs,
    )


def test_validator_reports_duplicate_missing_dependency_and_bad_input_reference() -> None:
    dag = DagDefinition(
        dag_id="dag_01",
        version=1,
        nodes=(
            node("extract"),
            node("extract", depends_on=("missing",), inputs=(InputRef(source_task_id="unknown"),)),
        ),
    )

    reasons = {issue.reason for issue in validate_dag(dag)}

    assert reasons == {"duplicate_node_id:extract", "missing_node"}
