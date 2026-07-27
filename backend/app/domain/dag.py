from typing import Any, Literal

from pydantic import Field

from app.domain.models import DomainModel


class InputRef(DomainModel):
    source_task_id: str | None = None
    source_path: str | None = None
    value: dict[str, Any] | None = None


class RetryPolicy(DomainModel):
    max_attempts: int = Field(default=1, ge=1, le=10)
    retryable_codes: tuple[str, ...] = ()


class DagCapability(DomainModel):
    name: str
    version: str = Field(pattern=r"^v[1-9][0-9]*$")


class DagNode(DomainModel):
    node_id: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")
    type: Literal["map", "reduce", "final_reduce", "review"]
    objective: str = Field(min_length=1)
    depends_on: tuple[str, ...] = ()
    inputs: tuple[InputRef, ...] = ()
    output_contract: str
    required_capabilities: tuple[DagCapability, ...]
    timeout_ms: int = Field(gt=0)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    optional: bool = False
    priority: int = 50


class DagEdge(DomainModel):
    from_node: str
    to_node: str


class DagDefinition(DomainModel):
    dag_id: str
    version: int = Field(ge=1)
    nodes: tuple[DagNode, ...] = Field(min_length=1)
    edges: tuple[DagEdge, ...] = ()
