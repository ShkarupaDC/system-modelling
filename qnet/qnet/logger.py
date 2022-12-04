from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Mapping, Iterable
from typing import Callable, Generic, TypeVar, Any

import prettytable as pt

from .common import T, I, SupportsDict, Metrics
from .node import Node, NodeMetrics
from .model import EvaluationReport, ModelMetrics

M_contra = TypeVar('M_contra', bound=Metrics, contravariant=True)
N_contra = TypeVar('N_contra', bound=Node, contravariant=True)

LoggerDispatcher = Callable[[T], dict[str, Any]]
NodeLoggerDispatcher = LoggerDispatcher[N_contra]
MetricsLoggerDispatcher = LoggerDispatcher[M_contra]


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
        self.table_kwargs = dict(align='l', max_width=max_column_width, max_table_width=max_table_width)

    # Formatters
    def _format(self, value: Any) -> str:
        if isinstance(value, SupportsDict):
            return self._format_class(value, self._to_dict(value))
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
                     start_chars: str = '',
                     sort_by_key: bool = False) -> str:
        items: Iterable = dict_.items()
        if sort_by_key:
            items = sorted(items)
        dict_str = join_chars.join(f'{key}{split_chars}{self._format(value)}' for key, value in items)
        return f'{start_chars}{dict_str}'

    def _format_iter(self, iter_: Iterable, join_chars: str = ', ', with_braces: bool = True) -> str:
        iter_str = join_chars.join(map(self._format, iter_))
        if with_braces:
            try:
                lbrace, rbrace = tuple(str(type(iter_)()))
            except Exception:  # pylint: disable=broad-except
                lbrace, rbrace = '[', ']'
            return f'{lbrace}{iter_str}{rbrace}'
        return iter_str

    def _format_class(self, value: Any, info: Any) -> str:
        return f'{type(value).__name__}({self._format(info)})'

    def _format_metrics_dict(self, metrics_dict: dict[str, Any]) -> str:
        out_metrics_dict: dict[str, Any] = {}
        for name, metrics in metrics_dict.items():
            if isinstance(metrics, dict):
                out_metrics_dict[name] = self._format_dict(metrics,
                                                           join_chars='\n',
                                                           split_chars=': ',
                                                           start_chars='\n',
                                                           sort_by_key=True)
            else:
                out_metrics_dict[name] = metrics
        return self._format_dict(out_metrics_dict, join_chars='\n', split_chars=': ', sort_by_key=True)

    # Other
    def _to_dict(self, value: SupportsDict) -> dict[str, Any]:
        return value.to_dict()

    # Node state
    def _dispatch_node_logger(self, node: Node[I, NodeMetrics]) -> NodeLoggerDispatcher:
        if isinstance(node, SupportsDict):
            return self._to_dict
        raise RuntimeError(f'{type(node)} must be inherited from "Node"')

    # Node metrics
    def _dispatch_node_metrics_logger(self, metrics: NodeMetrics) -> MetricsLoggerDispatcher:
        if isinstance(metrics, SupportsDict):
            return self._to_dict
        raise RuntimeError(f'{type(metrics)} must be inherited from "NodeMetrics"')

    # Model metrics
    def _dispatch_model_metrics_logger(self, metrics: ModelMetrics[I]) -> MetricsLoggerDispatcher:
        if isinstance(metrics, ModelMetrics):
            return self._to_dict
        raise RuntimeError(f'{type(metrics)} must be inherited from "ModelMetrics"')

    # Interface
    def nodes_states(self, time: float, nodes: list[Node[I, NodeMetrics]]) -> None:
        table = pt.PrettyTable(field_names=['Node', 'State', 'Action'], **self.table_kwargs)
        for node in nodes:
            state_dict = self._dispatch_node_logger(node)(node)
            action = ('end' if node.metrics.end_action_time == time else
                      'start' if node.metrics.start_action_time == time else '--')
            table.add_row([node.name, self._format(state_dict), action])
        print(f'Time: {self._format(time)}')
        print(table.get_string(title='Nodes States', hrules=pt.ALL, sortby='Node'))

    def model_metrics(self, model_metrics: ModelMetrics[I]) -> None:
        table = pt.PrettyTable(field_names=['Metrics'], **self.table_kwargs)
        metrics_dict = self._dispatch_model_metrics_logger(model_metrics)(model_metrics)
        table.add_row([self._format_metrics_dict(metrics_dict)])
        print(table.get_string(title='Model Metrics'))

    def nodes_metrics(self, nodes_metrics: list[NodeMetrics]) -> None:
        table = pt.PrettyTable(field_names=['Node', 'Metrics'], **self.table_kwargs)
        for metrics in nodes_metrics:
            metrics_dict = self._dispatch_node_metrics_logger(metrics)(metrics)
            table.add_row([metrics.node_name, self._format_metrics_dict(metrics_dict)])
        print(table.get_string(title='Nodes Metrics', hrules=pt.ALL, sortby='Node'))

    def evaluation_reports(self, evaluation_reports: list[EvaluationReport]) -> None:
        table = pt.PrettyTable(field_names=['Report', 'Result'], **self.table_kwargs)
        for report in evaluation_reports:
            table.add_row([report.name, self._format(report.result)])
        print(table.get_string(title='Evaluation Reports', hrules=pt.ALL, sortby='Report'))
