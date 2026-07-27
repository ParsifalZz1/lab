from app.services.dag_topology import topological_layers
from app.services.review_dag_generator import build_review_analysis_dag


def test_review_dag_generator_creates_parallel_map_reduce_plan() -> None:
    dag = build_review_analysis_dag(batch_count=3)

    assert [node.node_id for node in dag.nodes] == [
        "extract_batch_01",
        "extract_batch_02",
        "extract_batch_03",
        "reduce_findings",
        "final_recommendations",
    ]
    assert topological_layers(dag) == (
        ("extract_batch_01", "extract_batch_02", "extract_batch_03"),
        ("reduce_findings",),
        ("final_recommendations",),
    )
