import pytest

from app.domain.context import ContextPackage
from app.services.brain import FakeBrainPlanner, PlanningRequest, synthesize_review_report


def test_fake_brain_returns_deterministic_review_dag() -> None:
    dag = FakeBrainPlanner().plan(
        PlanningRequest(goal="Analyze product reviews", review_batch_count=2)
    )

    assert dag.nodes[-1].node_id == "final_recommendations"
    assert len(dag.nodes) == 4


def test_fake_brain_rejects_unsupported_goal() -> None:
    with pytest.raises(ValueError, match="only supports"):
        FakeBrainPlanner().plan(PlanningRequest(goal="Translate this document"))


def test_fake_brain_synthesizes_review_report() -> None:
    report = synthesize_review_report(
        ContextPackage(
            run_id="run",
            contract="review_summary.v1",
            content={"findings": [{"topic": "battery", "count": 3, "evidence": ["drains fast"]}]},
        )
    )

    assert report["top_issues"][0]["recommendation"] == "Prioritize improvements to battery."
