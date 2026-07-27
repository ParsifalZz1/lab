import pytest

from app.services.brain import FakeBrainPlanner, PlanningRequest


def test_fake_brain_returns_deterministic_review_dag() -> None:
    dag = FakeBrainPlanner().plan(
        PlanningRequest(goal="Analyze product reviews", review_batch_count=2)
    )

    assert dag.nodes[-1].node_id == "final_recommendations"
    assert len(dag.nodes) == 4


def test_fake_brain_rejects_unsupported_goal() -> None:
    with pytest.raises(ValueError, match="only supports"):
        FakeBrainPlanner().plan(PlanningRequest(goal="Translate this document"))
