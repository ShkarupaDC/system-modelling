from typing import Any

from qnet.common import T
from qnet.base import Node, Metrics
from qnet.logger import NodeLoggerDispatcher, MetricLoggerDispatcher, CLILogger

from .queueing import BQ, BankQueueingMetrics
from .transition import BankTransitionNode


class BankCLILogger(CLILogger[T]):

    def _bank_transition_node(self, node: BankTransitionNode[T]) -> dict[str, Any]:
        return {
            'next_node': node.next_node.name if node.next_node else None,
            'first_queue_size': node.first.queuelen,
            'second_queue_size': node.second.queuelen
        }

    def _bank_queueing_metrics(self, metrics: BankQueueingMetrics[BQ]) -> dict[str, Any]:
        metrics_dict = self._queueing_metrics(metrics)
        metrics_dict['num_switched_from_neighbor_checkout'] = metrics.num_from_neighbor
        return metrics_dict

    def _dispatch_node_logger(self, node: Node[T]) -> NodeLoggerDispatcher:
        if isinstance(node, BankTransitionNode):
            return self._bank_transition_node
        return super()._dispatch_node_logger(node)

    def _dispatch_metrics_logger(self, metrics: Metrics[Node[T]]) -> MetricLoggerDispatcher:
        if isinstance(metrics, BankQueueingMetrics):
            return self._bank_queueing_metrics
        return super()._dispatch_metrics_logger(metrics)
