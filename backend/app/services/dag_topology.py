from collections import defaultdict, deque

from app.domain.dag import DagDefinition


class DagCycleError(ValueError):
    pass


def topological_layers(dag: DagDefinition) -> tuple[tuple[str, ...], ...]:
    dependencies = {node.node_id: set(node.depends_on) for node in dag.nodes}
    for edge in dag.edges:
        dependencies[edge.to_node].add(edge.from_node)
    children: dict[str, set[str]] = defaultdict(set)
    for node_id, node_dependencies in dependencies.items():
        for dependency in node_dependencies:
            children[dependency].add(node_id)
    ready = deque(sorted(node_id for node_id, deps in dependencies.items() if not deps))
    layers: list[tuple[str, ...]] = []
    resolved = 0
    while ready:
        layer = tuple(ready)
        ready.clear()
        layers.append(layer)
        for node_id in layer:
            resolved += 1
            for child in sorted(children[node_id]):
                dependencies[child].remove(node_id)
                if not dependencies[child]:
                    ready.append(child)
    if resolved != len(dependencies):
        remaining = sorted(node_id for node_id, deps in dependencies.items() if deps)
        raise DagCycleError(f"DAG contains a cycle: {', '.join(remaining)}")
    return tuple(layers)


def initial_ready_nodes(dag: DagDefinition) -> tuple[str, ...]:
    return topological_layers(dag)[0]
