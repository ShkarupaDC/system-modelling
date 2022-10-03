from typing import Callable, Generic

from .common import T
from .base import Node, Metrics
from .factory import FactoryNode
from .queueing import Handler, MinHeap, Queue, QueueingNode, QueueingMetrics
from .transition import ProbaTransitionNode

NodeLoggerDispatcher = Callable[[Node[T]], str]
MetricLoggerDispatcher = Callable[[Metrics[Node[T]]], str]


class Logger(Generic[T]):

    def __init__(self, precision: int = 3) -> None:
        self.precision = precision

    def _base_node(self, node: Node[T], addon: str) -> str:
        return f'{node.name}({addon})'

    def node(self, node: Node[T]) -> str:
        return self._base_node(node, f'next_time={node.next_time:.{self.precision}f}, '
                               f'num_out={node.metrics.num_out}')

    def node_metrics(self, metrics: Metrics[Node[T]]) -> str:
        return f'Num in items: {metrics.num_in}. Num out items: {metrics.num_out}'

    def factory_item_node(self, node: FactoryNode) -> str:
        return self.node(node)

    def handler(self, handler: Handler) -> str:
        return f'Handler(item={handler.item}, next_time={handler.next_time:.{self.precision}f})'

    def handlers(self, handlers: MinHeap[Handler]) -> str:
        return ('Handlers('
                f'max_handlers={handlers.maxlen}, '
                f'handlers={[self.handler(handler) for handler in handlers.heap]})')

    def queue(self, queue: Queue[T]) -> str:
        return f'Queue(max_size={queue.maxlen}, items={list(queue.queue)})'

    def queueing_node(self, node: QueueingNode[T]) -> str:
        return self._base_node(
            node, f'next_time={node.next_time}, '
            f'num_out={node.metrics.num_out}, '
            f'handlers={self.handlers(node.handlers)}, '
            f'queue={self.queue(node.queue)}, '
            f'num_failures={node.metrics.num_failures}')

    def queueing_metrics(self, metrics: QueueingMetrics[T]) -> str:
        return (f'Num processed: {metrics.num_out}. '
                f'Mean queue size: {metrics.mean_queuelen:.{self.precision}f}. '
                f'Mean busy handlers: {metrics.mean_busy_handlers:.{self.precision}f}. '
                f'Mean wait time: {metrics.mean_wait_time:.{self.precision}f}. '
                f'Failure probability: {metrics.failure_proba:.{self.precision}f}')

    def proba_transition_node(self, node: ProbaTransitionNode[T]) -> str:
        return self._base_node(node, f'item={node.item}, '
                               f'next_node={node.next_node.name if node.next_node else None}')

    def get_node_logger(self, node: Node[T]) -> NodeLoggerDispatcher:
        if isinstance(node, FactoryNode):
            return self.factory_item_node
        if isinstance(node, QueueingNode):
            return self.queueing_node
        if isinstance(node, ProbaTransitionNode):
            return self.proba_transition_node
        if isinstance(node, Node):
            return self.node
        raise RuntimeError(f'{type(node)} must be inherited from "Node"')

    def get_metrics_logger(self, metrics: Metrics[Node[T]]) -> MetricLoggerDispatcher:
        if isinstance(metrics, QueueingMetrics):
            return self.queueing_metrics
        if isinstance(metrics, Metrics):
            return self.node_metrics
        raise RuntimeError(f'{type(metrics)} must be inherited from "Metrics"')

    def log_state(self, time: float, nodes: list[Node[T]]) -> None:
        print('-------------------------------State-------------------------------')
        updated = [node.name for node in nodes if node.current_time == time]
        print(f'{time:.{self.precision}f}. '
              f'Updated: {updated}. '
              f"State: {', '.join(self.get_node_logger(node)(node) for node in nodes)}")

    def log_metrics(self, nodes_metrics: list[Metrics[Node[T]]]) -> None:
        print('------------------------------Metrics------------------------------')
        print('\n'.join(f'{metrics.node.name}:\n{self.get_metrics_logger(metrics)(metrics)}'
                        for metrics in nodes_metrics))
