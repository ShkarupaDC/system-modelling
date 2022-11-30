from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Mapping, Iterable
from typing import TYPE_CHECKING, Callable, Generic, Any

import prettytable as pt

from qnet.common import T
from qnet.base import Item, Node, Metrics, NodeMetrics
from qnet.factory import BaseFactoryNode, FactoryMetrics
from qnet.queueing import Channel, BoundedCollection, QueueingNode, QueueingMetrics
from qnet.transition import BaseTransitionNode

if TYPE_CHECKING:
    from .model import Model, EvaluationReport, ModelMetrics

NodeLoggerDispatcher = Callable[[Node[T]], dict[str, Any]]
MetricLoggerDispatcher = Callable[[Metrics[Node[T]]], dict[str, Any]]


def _format_float(value: float, precision: str = 3) -> str:
    return f'{value:.{precision}f}'


class BaseLogger(ABC, Generic[T]):

    @abstractmethod
    def nodes_states(self, time: float, nodes: list[Node[T]], updated_nodes: list[Node[T]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def model_metrics(self, model_metrics: ModelMetrics[Model[T]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def nodes_metrics(self, nodes_metrics: list[NodeMetrics[Node[T]]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def evaluation_reports(self, evaluation_reports: list[EvaluationReport]) -> None:
        raise NotImplementedError


class CLILogger(BaseLogger[T]):

    def __init__(self, precision: int = 3, max_column_width: int = 60, max_table_width: int = 100) -> None:
        self.precision = precision
        self.max_column_width = max_column_width
        self.max_table_width = max_table_width

    # Formatters
    def _format(self, value: Any) -> str:
        class_name = value.__class__.__name__
        if isinstance(value, Channel):
            return f'{class_name}({self._format(self._channel(value))})'
        if isinstance(value, BoundedCollection):
            return f'{class_name}({self._format(self._bounded_collection(value))})'
        if isinstance(value, Mapping):
            return self._format_dict(value)
        if isinstance(value, Iterable) and not isinstance(value, str):
            return self._format_iter(value)
        if isinstance(value, float):
            return _format_float(value, self.precision)
        return str(value)

    def _format_dict(self,
                     dict_: Mapping,
                     join_chars: str = ', ',
                     split_chars: str = '=',
                     start_chars: str = '') -> str:
        dict_str = join_chars.join(f'{key}{split_chars}{self._format(value)}' for key, value in dict_.items())
        return f'{start_chars}{dict_str}'

    def _format_iter(self, iter_: Iterable, join_chars: str = ', ', with_braces: bool = True) -> str:
        iter_str = join_chars.join(map(self._format, iter_))
        return f'[{iter_str}]' if with_braces else iter_str

    # Other
    def _channel(self, channel: Channel) -> dict[str, Any]:
        return {'item': channel.item, 'next_time': channel.next_time}

    def _bounded_collection(self, collection: BoundedCollection[T]) -> dict[str, Any]:
        return {'max_size': collection.maxlen, 'items': list(collection.data)}

    # Node state
    def _node(self, node: Node[T]) -> dict[str, Any]:
        return {'next_time': node.next_time}

    def _base_factory_node(self, node: BaseFactoryNode[T]) -> dict[str, Any]:
        node_dict = self._node(node)
        node_dict['item'] = node.item
        if isinstance(node.item, Item):
            node_dict['created'] = node.item.created_time
        return node_dict

    def _queueing_node(self, node: QueueingNode[T]) -> dict[str, Any]:
        node_dict = self._node(node)
        node_dict.update({'channels': node.channels, 'queue': node.queue, 'num_failures': node.metrics.num_failures})
        return node_dict

    def _base_transition_node(self, node: BaseTransitionNode[T]) -> dict[str, Any]:
        return {'item': node.item, 'next_node': node.next_node.name if node.next_node else None}

    def _dispatch_node_logger(self, node: Node[T]) -> NodeLoggerDispatcher:
        if isinstance(node, QueueingNode):
            return self._queueing_node
        if isinstance(node, BaseTransitionNode):
            return self._base_transition_node
        if isinstance(node, BaseFactoryNode):
            return self._base_factory_node
        if isinstance(node, Node):
            return self._node
        raise RuntimeError(f'{type(node)} must be inherited from "Node"')

    # Node metrics
    def _node_metrics(self, metrics: NodeMetrics[Node[T]]) -> dict[str, Any]:
        return {'num_in_items': metrics.num_in, 'num_out_items': metrics.num_out}

    def _factory_metrics(self, metrics: FactoryMetrics[T]) -> dict[str, Any]:
        metrics_dict = self._node_metrics(metrics)
        metrics_dict['mean_time_in_system'] = metrics.mean_time
        return metrics_dict

    def _queueing_metrics(self, metrics: QueueingMetrics[T]) -> dict[str, Any]:
        metrics_dict = self._node_metrics(metrics)
        metrics_dict.update({
            'mean_interval_between_in_actions': metrics.mean_in_interval,
            'mean_interval_between_out_actions': metrics.mean_out_interval,
            'mean_queue_size': metrics.mean_queuelen,
            'mean_busy_channels': metrics.mean_busy_channels,
            'mean_wait_time': metrics.mean_wait_time,
            'mean_processing_time': metrics.mean_busy_time,
            'failure_probability': metrics.failure_proba,
        })
        return metrics_dict

    def _dispatch_metrics_logger(self, metrics: NodeMetrics[Node[T]]) -> MetricLoggerDispatcher:
        if isinstance(metrics, QueueingMetrics):
            return self._queueing_metrics
        if isinstance(metrics, FactoryMetrics):
            return self._factory_metrics
        if isinstance(metrics, NodeMetrics):
            return self._node_metrics
        raise RuntimeError(f'{type(metrics)} must be inherited from "NodeMetrics"')

    # Model metrics
    def _model_metrics(self, metrics: ModelMetrics[Model[T]]) -> dict[str, Any]:
        return {'mum_events': metrics.num_events, 'mean_event_intensity': metrics.mean_event_intensity}

    # Interface
    def nodes_states(self, time: float, nodes: list[Node[T]], updated_nodes: list[Node[T]]) -> None:
        table = pt.PrettyTable(field_names=['Node', 'State', 'Updated'],
                               align='l',
                               max_width=self.max_column_width,
                               max_table_width=self.max_table_width)
        updated_names = {node.name for node in updated_nodes}
        for node in nodes:
            state_dict = self._dispatch_node_logger(node)(node)
            table.add_row([node.name, self._format(state_dict), '+' if node.name in updated_names else '-'])
        print(f'Time: {_format_float(time, self.precision)}')
        print(table.get_string(title='Nodes States', hrules=pt.ALL, sortby='Node'))

    def model_metrics(self, model_metrics: ModelMetrics[Model[T]]) -> None:
        table = pt.PrettyTable(field_names=['Metrics'],
                               align='l',
                               max_width=self.max_column_width,
                               max_table_width=self.max_table_width)
        table.add_row([self._format_dict(self._model_metrics(model_metrics), join_chars='\n', split_chars=': ')])
        print(table.get_string(title='Model Metrics'))

    def nodes_metrics(self, nodes_metrics: list[NodeMetrics[Node[T]]]) -> None:
        table = pt.PrettyTable(field_names=['Node', 'Metrics'],
                               align='l',
                               max_width=self.max_column_width,
                               max_table_width=self.max_table_width)
        for metrics in nodes_metrics:
            metrics_dict = self._dispatch_metrics_logger(metrics)(metrics)
            table.add_row([metrics.parent.name, self._format_dict(metrics_dict, join_chars='\n', split_chars=": ")])
        print(table.get_string(title='Nodes Metrics', hrules=pt.ALL, sortby='Node'))

    def evaluation_reports(self, evaluation_reports: list[EvaluationReport]) -> None:
        table = pt.PrettyTable(field_names=['Report', 'Result'],
                               align='l',
                               max_width=self.max_column_width,
                               max_table_width=self.max_table_width)
        for report in evaluation_reports:
            table.add_row([report.name, self._format(report.result)])
        print(table.get_string(title='Evaluation Reports', hrules=pt.ALL, sortby='Report'))
