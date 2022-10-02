from typing import Generic, Any

from .common import INF_TIME, TIME_EPS, T
from .base import Node, Stats


class Model(Generic[T]):

    def __init__(self, nodes: list[Node[T]]) -> None:
        self.nodes = nodes

    def simulate(self, end_time: float, verbose: bool = False) -> dict[str, Stats]:
        current_time = 0
        while current_time < end_time:
            # Find next closest action
            next_time = INF_TIME
            for node in self.nodes:
                if node.next_time < next_time:
                    next_time = node.next_time
            # Move to that action
            current_time = next_time
            for node in self.nodes:
                node.update_time(current_time)
            # Run actions
            for node in self.nodes:
                if abs(next_time - node.next_time) < TIME_EPS:
                    node.end_action()
            # Log states
            if verbose:
                pass
                # self.log_nodes(current_time, self.nodes)
        nodes_stats = {node.name: node.stats for node in self.nodes}
        # Log stats
        # self.log_stats(nodes_stats)
        return nodes_stats

    @staticmethod
    def from_factory(factory: Node[T], **kwargs: Any) -> 'Model[T]':
        nodes: set[Node[T]] = set()

        def process_node(parent: Node[T]) -> None:
            nodes.add(parent)
            for node in parent.connected_nodes:
                if node not in nodes:
                    process_node(node)

        process_node(factory)
        return Model[T](nodes=list(nodes), **kwargs)
