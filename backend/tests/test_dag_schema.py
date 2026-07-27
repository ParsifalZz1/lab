from app.domain.dag import DagCapability, DagDefinition, DagEdge, DagNode, InputRef, RetryPolicy


def test_dag_schema_serializes_nodes_edges_and_retry_policy() -> None:
    node = DagNode(
        node_id="extract_batch_01",
        type="map",
        objective="Extract review findings",
        inputs=(InputRef(value={"batch_ref": "artifact://input/01"}),),
        output_contract="review_findings.v1",
        required_capabilities=(DagCapability(name="information_extraction", version="v1"),),
        timeout_ms=5_000,
        retry_policy=RetryPolicy(max_attempts=2, retryable_codes=("NETWORK_UNAVAILABLE",)),
    )
    dag = DagDefinition(
        dag_id="dag_01", version=1, nodes=(node,), edges=(DagEdge(from_node="a", to_node="b"),)
    )

    assert dag.model_dump(mode="json")["nodes"][0]["retry_policy"]["max_attempts"] == 2
