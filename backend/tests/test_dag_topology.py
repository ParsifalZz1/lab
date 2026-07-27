import pytest

from app.domain.dag import DagCapability, DagDefinition, DagNode
from app.services.dag_topology import DagCycleError, initial_ready_nodes, topological_layers


def node(node_id: str, depends_on: tuple[str, ...] = ()) -> DagNode:
    return DagNode(
        node_id=node_id,
        type="map",
        objective="Extract findings",
        depends_on=depends_on,
        output_contract="review_findings.v1",
        required_capabilities=(DagCapability(name="extract", version="v1"),),
        timeout_ms=1_000,
    )


def test_topological_layers_and_initial_ready_nodes() -> None:
    dag = DagDefinition(
        dag_id="dag_01", version=1, nodes=(node("a"), node("b"), node("c", ("a", "b")))
    )

    assert initial_ready_nodes(dag) == ("a", "b")
    assert topological_layers(dag) == (("a", "b"), ("c",))


def test_topological_sort_rejects_cycle() -> None:
    dag = DagDefinition(dag_id="dag_01", version=1, nodes=(node("a", ("b",)), node("b", ("a",))))

    with pytest.raises(DagCycleError, match="cycle"):
        topological_layers(dag)
