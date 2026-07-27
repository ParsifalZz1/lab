from pydantic import BaseModel

from app.domain.dag import DagDefinition


class DagValidationIssue(BaseModel):
    path: str
    reason: str


class DagValidationError(ValueError):
    def __init__(self, issues: list[DagValidationIssue]) -> None:
        self.issues = issues
        super().__init__("DAG validation failed")


def validate_dag(dag: DagDefinition) -> list[DagValidationIssue]:
    issues: list[DagValidationIssue] = []
    node_ids = [node.node_id for node in dag.nodes]
    node_id_set = set(node_ids)
    for node_id in node_id_set:
        if node_ids.count(node_id) > 1:
            issues.append(DagValidationIssue(path="nodes", reason=f"duplicate_node_id:{node_id}"))
    for index, node in enumerate(dag.nodes):
        if not node.required_capabilities:
            issues.append(
                DagValidationIssue(path=f"nodes[{index}].required_capabilities", reason="missing")
            )
        for dependency in node.depends_on:
            if dependency == node.node_id:
                issues.append(
                    DagValidationIssue(path=f"nodes[{index}].depends_on", reason="self_dependency")
                )
            elif dependency not in node_id_set:
                issues.append(
                    DagValidationIssue(path=f"nodes[{index}].depends_on", reason="missing_node")
                )
        for input_index, input_ref in enumerate(node.inputs):
            if input_ref.source_task_id and input_ref.source_task_id not in node_id_set:
                issues.append(
                    DagValidationIssue(
                        path=f"nodes[{index}].inputs[{input_index}].source_task_id",
                        reason="missing_node",
                    )
                )
            if input_ref.source_task_id is None and input_ref.value is None:
                issues.append(
                    DagValidationIssue(
                        path=f"nodes[{index}].inputs[{input_index}]", reason="empty_input"
                    )
                )
    for edge_index, edge in enumerate(dag.edges):
        if edge.from_node not in node_id_set or edge.to_node not in node_id_set:
            issues.append(DagValidationIssue(path=f"edges[{edge_index}]", reason="missing_node"))
    return issues


def ensure_valid_dag(dag: DagDefinition) -> None:
    issues = validate_dag(dag)
    if issues:
        raise DagValidationError(issues)
