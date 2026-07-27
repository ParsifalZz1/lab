from app.domain.context import ContextPackage


def test_context_package_is_json_serializable() -> None:
    package = ContextPackage(
        run_id="run_01", contract="review_summary.v1", content={"findings": []}
    )

    assert package.model_dump(mode="json")["contract"] == "review_summary.v1"
