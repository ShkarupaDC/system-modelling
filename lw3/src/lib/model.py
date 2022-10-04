from typing import Generic, Any, Optional

from .common import INF_TIME, TIME_EPS, T
from .base import Node, Metrics
from .logger import Logger


class Model(Generic[T]):

    def __init__(self, nodes: list[Node[T]], logger: Logger = Logger()) -> None:
        self.nodes = nodes
        self.logger = logger

    def simulate(self, end_time: float, verbose: bool = False) -> list[Metrics]:
        current_time = 0
        while current_time < end_time:
            # Find next closest action
            next_time = INF_TIME
            for node in self.nodes:
                if node.next_time < next_time:
                    next_time = node.next_time
            if next_time > end_time:
                break
            # Move to that action
            current_time = next_time
            for node in self.nodes:
                node.update_time(current_time)
            # Run actions
            updated_nodes: list[Node[T]] = []
            for node in self.nodes:
                if abs(next_time - node.next_time) < TIME_EPS:
                    updated_nodes.append(node)
                    node.end_action()
            # Log states
            if verbose:
                self.logger.log_state(current_time, self.nodes, updated_nodes)
        nodes_metrics = [node.metrics for node in self.nodes]
        # Log stats
        self.logger.log_metrics(nodes_metrics)
        return nodes_metrics

    @staticmethod
    def from_factory(factory: Node[T], **kwargs: Any) -> 'Model[T]':
        nodes: set[Node[T]] = set()

        def process_node(parent: Optional[Node[T]]) -> None:
            if parent is None:
                return
            nodes.add(parent)
            for node in parent.connected_nodes:
                if node not in nodes:
                    process_node(node)

        process_node(factory)
        return Model[T](nodes=list(nodes), **kwargs)
