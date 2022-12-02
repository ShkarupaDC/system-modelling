from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Mapping, Iterable
from typing import Callable, Generic, Any

import prettytable as pt

from .common import T, I, BoundedCollection, Metrics, Item
from .node import Node, NodeMetrics
from .factory import BaseFactoryNode
from .queueing import Channel, QueueingNode, QueueingMetrics
from .transition import BaseTransitionNode
from .model import EvaluationReport, ModelMetrics

LoggerDispatcher = Callable[[T], dict[str, Any]]
NodeLoggerDispatcher = LoggerDispatcher[Node[Item, NodeMetrics]]
MetricsLoggerDispatcher = LoggerDispatcher[Metrics]


class BaseLogger(ABC, Generic[I]):

    @abstractmethod
    def nodes_states(self, time: float, nodes: list[Node[I, NodeMetrics]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def model_metrics(self, model_metrics: ModelMetrics) -> None:
        raise NotImplementedError

    @abstractmethod
    def nodes_metrics(self, nodes_metrics: list[NodeMetrics]) -> None:
        raise NotImplementedError

    @abstractmethod
    def evaluation_reports(self, evaluation_reports: list[EvaluationReport]) -> None:
        raise NotImplementedError


class CLILogger(BaseLogger[I]):

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
            return self._format_float(value)
        return str(value)

    def _format_float(self, float_: float) -> str:
        return f'{float_:.{self.precision}f}'

    def _format_dict(self,
                     dict_: Mapping,
                     join_chars: str = ', ',
                     split_chars: str = '=',
                     start_chars: str = '') -> str:
        dict_str = join_chars.join(f'{key}{split_chars}{self._format(value)}' for key, value in dict_.items())
        return f'{start_chars}{dict_str}'

    def _format_iter(self, iter_: Iterable, join_chars: str = ', ', with_braces: bool = True) -> str:
        iter_str = join_chars.join(map(self._format, iter_))
        if with_braces:
            try:
                left, right = tuple(str(iter_.__class__()))
            except ValueError:
                left, right = '[', ']'
            return f'{left}{iter_str}{right}'
        return iter_str

    # Other
    def _channel(self, channel: Channel[I]) -> dict[str, Any]:
        return {'item': channel.item, 'next_time': channel.next_time}

    def _bounded_collection(self, collection: BoundedCollection[I]) -> dict[str, Any]:
        return {'max_size': collection.maxlen, 'items': list(collection.data)}

    # Node state
    def _node(self, node: Node[I, NodeMetrics]) -> dict[str, Any]:
        return {'next_time': node.next_time}

    def _base_factory_node(self, node: BaseFactoryNode[I, NodeMetrics]) -> dict[str, Any]:
        node_dict = self._node(node)
        if node.item is not None:
            node_dict.update({'last_item': node.item, 'last_created_time': node.item.created_time})
        return node_dict

    def _queueing_node(self, node: QueueingNode[I, QueueingMetrics]) -> dict[str, Any]:
        node_dict = self._node(node)
        node_dict.update({'channels': node.channels, 'queue': node.queue, 'num_failures': node.metrics.num_failures})
        return node_dict

    def _base_transition_node(self, node: BaseTransitionNode[I, NodeMetrics]) -> dict[str, Any]:
        return {'item': node.item, 'next_node': node.next_node.name if node.next_node else None}

    def _dispatch_node_logger(self, node: Node[I, NodeMetrics]) -> NodeLoggerDispatcher:
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
    def _node_metrics(self, metrics: NodeMetrics) -> dict[str, Any]:
        return {'num_in_items': metrics.num_in, 'num_out_items': metrics.num_out}

    def _queueing_metrics(self, metrics: QueueingMetrics) -> dict[str, Any]:
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

    def _dispatch_node_metrics_logger(self, metrics: NodeMetrics) -> MetricsLoggerDispatcher:
        if isinstance(metrics, QueueingMetrics):
            return self._queueing_metrics
        if isinstance(metrics, NodeMetrics):
            return self._node_metrics
        raise RuntimeError(f'{type(metrics)} must be inherited from "NodeMetrics"')

    # Model metrics
    def _model_metrics(self, metrics: ModelMetrics) -> dict[str, Any]:
        return {
            'mum_events': metrics.num_events,
            'mean_event_intensity': metrics.mean_event_intensity,
            'mean_time_in_system': metrics.mean_time
        }

    def _dispatch_model_metrics_logger(self, metrics: ModelMetrics[I]) -> MetricsLoggerDispatcher:
        if isinstance(metrics, ModelMetrics):
            return self._model_metrics
        raise RuntimeError(f'{type(metrics)} must be inherited from "ModelMetrics"')

    # Interface
    def nodes_states(self, time: float, nodes: list[Node[I, NodeMetrics]]) -> None:
        table = pt.PrettyTable(field_names=['Node', 'State', 'Action'],
                               align='l',
                               max_width=self.max_column_width,
                               max_table_width=self.max_table_width)
        for node in nodes:
            state_dict = self._dispatch_node_logger(node)(node)
            action = ('end' if node.metrics.end_action_time == time else
                      'start' if node.metrics.start_action_time == time else '--')
            table.add_row([node.name, self._format(state_dict), action])
        print(f'Time: {self._format_float(time)}')
        print(table.get_string(title='Nodes States', hrules=pt.ALL, sortby='Node'))

    def model_metrics(self, model_metrics: ModelMetrics[I]) -> None:
        table = pt.PrettyTable(field_names=['Metrics'],
                               align='l',
                               max_width=self.max_column_width,
                               max_table_width=self.max_table_width)
        metrics_dict = self._dispatch_model_metrics_logger(model_metrics)(model_metrics)
        table.add_row([self._format_dict(metrics_dict, join_chars='\n', split_chars=': ')])
        print(table.get_string(title='Model Metrics'))

    def nodes_metrics(self, nodes_metrics: list[NodeMetrics]) -> None:
        table = pt.PrettyTable(field_names=['Node', 'Metrics'],
                               align='l',
                               max_width=self.max_column_width,
                               max_table_width=self.max_table_width)
        for metrics in nodes_metrics:
            metrics_dict = self._dispatch_node_metrics_logger(metrics)(metrics)
            table.add_row([metrics.node_name, self._format_dict(metrics_dict, join_chars='\n', split_chars=": ")])
        print(table.get_string(title='Nodes Metrics', hrules=pt.ALL, sortby='Node'))

    def evaluation_reports(self, evaluation_reports: list[EvaluationReport]) -> None:
        table = pt.PrettyTable(field_names=['Report', 'Result'],
                               align='l',
                               max_width=self.max_column_width,
                               max_table_width=self.max_table_width)
        for report in evaluation_reports:
            table.add_row([report.name, self._format(report.result)])
        print(table.get_string(title='Evaluation Reports', hrules=pt.ALL, sortby='Report'))
