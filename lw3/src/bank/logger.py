from ..lib.common import T
from ..lib.base import Node, Metrics
from ..lib.logger import NodeLoggerDispatcher, MetricLoggerDispatcher, Logger

from .queueing import BQ, BankQueueingMetrics
from .transition import BankTransitionNode


class BankLogger(Logger[T]):

    def bank_transition_node(self, node: BankTransitionNode[T]) -> str:
        return self._base_node(
            node, f'next_node={node.next_node.name if node.next_node else None}, '
            f'first_queue_size={node.first.queuelen}, '
            f'second_queue_size={node.second.queuelen}')

    def bank_queueing_metrics(self, metrics: BankQueueingMetrics[BQ]) -> str:
        return (f'{self.queueing_metrics(metrics)}. '
                f'Num switched from neighbor checkout: {metrics.num_from_neighbor}')

    def get_node_logger(self, node: Node[T]) -> NodeLoggerDispatcher:
        if isinstance(node, BankTransitionNode):
            return self.bank_transition_node
        return super().get_node_logger(node)

    def get_metrics_logger(self, metrics: Metrics[Node[T]]) -> MetricLoggerDispatcher:
        if isinstance(metrics, BankQueueingMetrics):
            return self.bank_queueing_metrics
        return super().get_metrics_logger(metrics)
