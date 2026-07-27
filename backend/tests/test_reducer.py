from app.services.reducer import reduce_review_findings


def test_reducer_deduplicates_evidence_and_preserves_sources() -> None:
    reduced = reduce_review_findings(
        [
            {
                "task_id": "a",
                "attempt_id": "aa",
                "worker_id": "w1",
                "findings": [{"topic": "battery", "count": 2, "evidence": ["drains fast"]}],
            },
            {
                "task_id": "b",
                "attempt_id": "bb",
                "worker_id": "w2",
                "findings": [
                    {"topic": "battery", "count": 1, "evidence": ["drains fast", "dies early"]}
                ],
            },
        ]
    )

    assert reduced["findings"][0]["count"] == 3
    assert reduced["findings"][0]["evidence"] == ["dies early", "drains fast"]
    assert len(reduced["findings"][0]["sources"]) == 2
