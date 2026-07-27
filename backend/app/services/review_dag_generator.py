from app.domain.dag import DagCapability, DagDefinition, DagNode, InputRef


def build_review_analysis_dag(batch_count: int = 50) -> DagDefinition:
    if batch_count < 1:
        raise ValueError("batch_count must be positive")
    extraction_capability = DagCapability(name="information_extraction", version="v1")
    map_nodes = tuple(
        DagNode(
            node_id=f"extract_batch_{index:02d}",
            type="map",
            objective="Extract verifiable product issues and evidence from a review batch",
            inputs=(InputRef(value={"batch_index": index}),),
            output_contract="review_findings.v1",
            required_capabilities=(extraction_capability,),
            timeout_ms=15_000,
        )
        for index in range(1, batch_count + 1)
    )
    map_node_ids = tuple(node.node_id for node in map_nodes)
    reduce_node = DagNode(
        node_id="reduce_findings",
        type="reduce",
        objective="Merge and rank review findings across all batches",
        depends_on=map_node_ids,
        inputs=tuple(
            InputRef(source_task_id=node_id, source_path="findings") for node_id in map_node_ids
        ),
        output_contract="review_summary.v1",
        required_capabilities=(DagCapability(name="structured_json_generation", version="v1"),),
        timeout_ms=20_000,
    )
    final_node = DagNode(
        node_id="final_recommendations",
        type="final_reduce",
        objective=(
            "Produce the top product issues, supporting evidence, and improvement recommendations"
        ),
        depends_on=(reduce_node.node_id,),
        inputs=(InputRef(source_task_id=reduce_node.node_id),),
        output_contract="review_report.v1",
        required_capabilities=(DagCapability(name="result_synthesis", version="v1"),),
        timeout_ms=20_000,
    )
    return DagDefinition(
        dag_id="review_analysis", version=1, nodes=(*map_nodes, reduce_node, final_node)
    )
