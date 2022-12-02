from typing import Any

from qnet.common import I
from qnet.node import Node, NodeMetrics
from qnet.logger import NodeLoggerDispatcher, MetricsLoggerDispatcher, CLILogger

from .queueing import BankQueueingMetrics
from .transition import BankTransitionNode


class BankCLILogger(CLILogger[I]):

    def _bank_transition_node(self, node: BankTransitionNode[I, NodeMetrics]) -> dict[str, Any]:
        return {
            'next_node': node.next_node.name if node.next_node else None,
            'first_queue_size': node.first.queuelen,
            'second_queue_size': node.second.queuelen
        }

    def _dispatch_node_logger(self, node: Node[I, NodeMetrics]) -> NodeLoggerDispatcher:
        if isinstance(node, BankTransitionNode):
            return self._bank_transition_node
        return super()._dispatch_node_logger(node)

    def _bank_queueing_metrics(self, metrics: BankQueueingMetrics) -> dict[str, Any]:
        metrics_dict = self._queueing_metrics(metrics)
        metrics_dict['num_switched_from_neighbor_checkout'] = metrics.num_from_neighbor
        return metrics_dict

    def _dispatch_node_metrics_logger(self, metrics: NodeMetrics) -> MetricsLoggerDispatcher:
        if isinstance(metrics, BankQueueingMetrics):
            return self._bank_queueing_metrics
        return super()._dispatch_node_metrics_logger(metrics)
