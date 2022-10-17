from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Generic

from lib.common import T
from lib.base import Item, Node, Metrics, NodeMetrics
from lib.factory import BaseFactoryNode, FactoryMetrics
from lib.queueing import Channel, MinHeap, Queue, QueueingNode, QueueingMetrics
from lib.transition import BaseTransitionNode

if TYPE_CHECKING:
    from .model import Model, EvaluationReport, ModelMetrics

NodeLoggerDispatcher = Callable[[Node[T]], str]
MetricLoggerDispatcher = Callable[[Metrics[Node[T]]], str]


def _format_float(value: float, precision: str = 3) -> str:
    return f'{value:.{precision}f}'


class BaseLogger(ABC, Generic[T]):

    @abstractmethod
    def log_state(self, time: float, nodes: list[Node[T]], updated_nodes: list[Node[T]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def log_metrics(self, model_metrics: ModelMetrics[Model[T]], nodes_metrics: list[NodeMetrics[Node[T]]],
                    evaluations: list[EvaluationReport]) -> None:
        raise NotImplementedError


class Logger(BaseLogger[T]):

    def __init__(self, precision: int = 3) -> None:
        self.precision = precision

    def float(self, value: float) -> str:
        return _format_float(value, self.precision)

    def dashed_line(self, length: int) -> str:
        return '-' * length

    def _base_node(self, node: Node[T], addon: str) -> str:
        return f'{node.name}({addon})'

    def node(self, node: Node[T]) -> str:
        return self._base_node(node, f'next_time={self.float(node.next_time)}')

    def base_factory_node(self, node: BaseFactoryNode[T]) -> str:
        return self._base_node(
            node, f'next_time={self.float(node.next_time)}, '
            f'item={node.item}, ' +
            f'created={self.float(node.item.created_time)}' if isinstance(node.item, Item) else '')

    def channel(self, channel: Channel) -> str:
        return f'Channel(item={channel.item}, next_time={self.float(channel.next_time)})'

    def channels(self, channels: MinHeap[Channel]) -> str:
        return ('Channels('
                f'max_channels={channels.maxlen}, '
                f"channels=[{', '.join(self.channel(channel) for channel in channels.data)}])")

    def queue(self, queue: Queue[T]) -> str:
        return f'Queue(max_size={queue.maxlen}, items={list(queue.data)})'

    def queueing_node(self, node: QueueingNode[T]) -> str:
        return self._base_node(
            node, f'next_time={self.float(node.next_time)}, '
            f'channels={self.channels(node.channels)}, '
            f'queue={self.queue(node.queue)}, '
            f'num_failures={node.metrics.num_failures}')

    def base_transition_node(self, node: BaseTransitionNode[T]) -> str:
        return self._base_node(node, f'item={node.item}, '
                               f'next_node={node.next_node.name if node.next_node else None}')

    def get_node_logger(self, node: Node[T]) -> NodeLoggerDispatcher:
        if isinstance(node, QueueingNode):
            return self.queueing_node
        if isinstance(node, BaseTransitionNode):
            return self.base_transition_node
        if isinstance(node, BaseFactoryNode):
            return self.base_factory_node
        if isinstance(node, Node):
            return self.node
        raise RuntimeError(f'{type(node)} must be inherited from "Node"')

    def node_metrics(self, metrics: NodeMetrics[Node[T]]) -> str:
        return f'Num in items: {metrics.num_in}. Num out items: {metrics.num_out}'

    def factory_metrics(self, metrics: FactoryMetrics[T]) -> str:
        return (f'{self.node_metrics(metrics)}. '
                f'Mean time in system: {self.float(metrics.mean_time)}')

    def queueing_metrics(self, metrics: QueueingMetrics[T]) -> str:
        return (f'{self.node_metrics(metrics)}. '
                f'Mean interval between input actions: {self.float(metrics.mean_in_interval)}. '
                f'Mean interval between output actions: {self.float(metrics.mean_out_interval)}. '
                f'Mean queue size: {self.float(metrics.mean_queuelen)}. '
                f'Mean busy channels: {self.float(metrics.mean_busy_channels)}. '
                f'Mean wait time: {self.float(metrics.mean_wait_time)}. '
                f'Mean processing time: {self.float(metrics.mean_busy_time)}. '
                f'Failure probability: {self.float(metrics.failure_proba)}')

    def get_metrics_logger(self, metrics: NodeMetrics[Node[T]]) -> MetricLoggerDispatcher:
        if isinstance(metrics, QueueingMetrics):
            return self.queueing_metrics
        if isinstance(metrics, FactoryMetrics):
            return self.factory_metrics
        if isinstance(metrics, NodeMetrics):
            return self.node_metrics
        raise RuntimeError(f'{type(metrics)} must be inherited from "Metrics"')

    def model_metrics(self, metrics: ModelMetrics[Model[T]]) -> str:
        return (f'Num events: {metrics.num_events}. '
                f'Mean event intensity {self.float(metrics.mean_event_intensity)}')

    def log_state(self, time: float, nodes: list[Node[T]], updated_nodes: list[Node[T]]) -> None:
        print(f'{self.dashed_line(31)}State{self.dashed_line(31)}')
        if nodes:
            updated = [node.name for node in sorted(updated_nodes, key=lambda node: node.name)]
            print(f'{self.float(time)}. End action happened: {updated}. After:')
            print('\n'.join(self.get_node_logger(node)(node) for node in sorted(nodes, key=lambda node: node.name)))

    def log_metrics(self, model_metrics: ModelMetrics[Model[T]], nodes_metrics: list[NodeMetrics[Node[T]]],
                    evaluations: list[EvaluationReport]) -> None:
        print(f'{self.dashed_line(30)}Metrics{self.dashed_line(30)}')

        print(f'Model Metrics:\n{self.model_metrics(model_metrics)}\n{self.dashed_line(30)}')
        if nodes_metrics:
            sorted_metrics = sorted(nodes_metrics, key=lambda metrics: metrics.parent.name)
            print(f'\n{self.dashed_line(30)}\n'.join(
                f'{metrics.parent.name}:\n{self.get_metrics_logger(metrics)(metrics)}' for metrics in sorted_metrics))
        if evaluations:
            print(f'{self.dashed_line(30)}\nExternal Evaluations:')
            print('. '.join(f'{evaluation.name}: {evaluation.report}'
                            for evaluation in sorted(evaluations, key=lambda evaluation: evaluation.name)))
