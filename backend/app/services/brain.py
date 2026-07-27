from typing import Protocol

from pydantic import BaseModel, Field

from app.domain.context import ContextPackage
from app.domain.dag import DagDefinition
from app.services.review_dag_generator import build_review_analysis_dag


class PlanningRequest(BaseModel):
    goal: str = Field(min_length=1)
    review_batch_count: int = Field(default=50, ge=1, le=500)


class BrainPlanner(Protocol):
    def plan(self, request: PlanningRequest) -> DagDefinition: ...


class FakeBrainPlanner:
    def plan(self, request: PlanningRequest) -> DagDefinition:
        if "review" not in request.goal.lower() and "评论" not in request.goal:
            raise ValueError("FakeBrainPlanner only supports review analysis goals")
        return build_review_analysis_dag(request.review_batch_count)


def synthesize_review_report(context: ContextPackage) -> dict[str, object]:
    if context.contract != "review_summary.v1":
        raise ValueError("Fake report synthesis requires review_summary.v1")
    issues = []
    for finding in context.content.get("findings", [])[:3]:
        issues.append(
            {
                "topic": finding["topic"],
                "count": finding["count"],
                "evidence": finding.get("evidence", [])[:2],
                "recommendation": f"Prioritize improvements to {finding['topic']}.",
            }
        )
    return {"contract": "review_report.v1", "top_issues": issues, "degraded": context.degraded}
