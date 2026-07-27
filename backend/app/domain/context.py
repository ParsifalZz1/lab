from typing import Any

from app.domain.models import DomainModel


class ContextPackage(DomainModel):
    run_id: str
    contract: str
    content: dict[str, Any]
    artifact_ids: tuple[str, ...] = ()
    degraded: bool = False
