from collections import defaultdict
from typing import Any


def reduce_review_findings(results: list[dict[str, Any]]) -> dict[str, Any]:
    topics: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "evidence": [], "sources": []}
    )
    for result in results:
        source = {
            "task_id": result["task_id"],
            "attempt_id": result["attempt_id"],
            "worker_id": result["worker_id"],
        }
        for finding in result["findings"]:
            topic = finding["topic"]
            aggregate = topics[topic]
            aggregate["count"] += finding.get("count", 1)
            aggregate["evidence"] = sorted(
                set(aggregate["evidence"]) | set(finding.get("evidence", []))
            )
            if source not in aggregate["sources"]:
                aggregate["sources"].append(source)
    findings = [
        {"topic": topic, **aggregate}
        for topic, aggregate in sorted(
            topics.items(), key=lambda item: (-item[1]["count"], item[0])
        )
    ]
    return {"contract": "review_summary.v1", "findings": findings}
