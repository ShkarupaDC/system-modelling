import statistics
from enum import Flag
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Generic, Optional, TypeVar

from .common import INF_TIME, TIME_EPS, T, I, Metrics, Item
from .node import Node, NodeMetrics
from .factory import BaseFactoryNode
from .queueing import QueueingNode

if TYPE_CHECKING:
    from .logger import BaseLogger

MM = TypeVar('MM', bound='ModelMetrics')


class Nodes(dict[str, Node[I, NodeMetrics]]):

    @staticmethod
    def from_node_tree_root(node_tree_root: Node[I, NodeMetrics]) -> 'Nodes[I]':
        nodes = Nodes[I]()

        def process_node(parent: Node[I, NodeMetrics]) -> None:
            if parent.name in nodes:
                if nodes[parent.name] == parent:
                    return
                else:
                    raise ValueError('Nodes must have different names')
            nodes[parent.name] = parent
            for node in parent.connected_nodes:
                process_node(node)

        process_node(node_tree_root)
        return nodes


@dataclass(eq=False)
class EvaluationReport(Generic[T]):
    name: str
    result: T


@dataclass(eq=False)
class Evaluation(Generic[T]):
    name: str
    evaluate: Callable[['Model[Item, ModelMetrics]'], T]

    def __call__(self, model: 'Model[Item, ModelMetrics]') -> EvaluationReport[T]:
        return EvaluationReport[T](name=self.name, result=self.evaluate(model))


class Verbosity(Flag):
    NONE = 0b00
    STATE = 0b01
    METRICS = 0b10


@dataclass(eq=False)
class ModelMetrics(Metrics, Generic[I]):
    num_events: int = field(init=False, default=0)
    items: set[I] = field(init=False, default_factory=set)

    @property
    def mean_event_intensity(self) -> float:
        return self.num_events / max(self.passed_time, TIME_EPS)

    @property
    def time_per_item(self) -> dict[I, float]:
        return {item: item.current_time - item.created_time for item in self.items if item.processed}

    @property
    def mean_time(self) -> float:
        return statistics.mean(time_data) if (time_data := self.time_per_item.values()) else 0


class Model(Generic[I, MM]):

    def __init__(self,
                 nodes: Nodes[I],
                 logger: 'BaseLogger[I]',
                 metrics: MM,
                 evaluations: Optional[list[Evaluation]] = None) -> None:
        self.nodes = nodes
        self.logger = logger
        self.metrics = metrics
        self.evaluations = [] if evaluations is None else evaluations
        self.current_time = 0.0
        self.collect_items()

    @property
    def next_time(self) -> float:
        return min(INF_TIME, *(node.next_time for node in self.nodes.values()))

    @property
    def model_metrics(self) -> MM:
        return self.metrics

    @property
    def nodes_metrics(self) -> list[NodeMetrics]:
        return [node.metrics for node in self.nodes.values()]

    @property
    def evaluation_reports(self) -> list[EvaluationReport]:
        return [evaluation(self) for evaluation in self.evaluations]

    def reset_metrics(self) -> None:
        for node in self.nodes.values():
            node.reset_metrics()
        self.metrics.reset()

    def reset(self) -> None:
        self.current_time = 0
        for node in self.nodes.values():
            node.reset()
        self.metrics.reset()

    def simulate(self, end_time: float, verbosity: Verbosity = Verbosity.METRICS) -> None:
        while self.step(end_time):
            # Log states
            if Verbosity.STATE in verbosity:
                self.logger.nodes_states(self.current_time, list(self.nodes.values()))
        # Log metrics
        if Verbosity.METRICS in verbosity:
            self.logger.model_metrics(self.model_metrics)
            self.logger.nodes_metrics(self.nodes_metrics)
            self.logger.evaluation_reports(self.evaluation_reports)

    def step(self, end_time: float = INF_TIME) -> bool:
        next_time = self.next_time
        self.goto(next_time, end_time=end_time)
        return next_time <= end_time

    def goto(self, time: float, end_time: float = INF_TIME) -> None:
        new_current_time = min(time, end_time)
        self._before_time_update_hook(new_current_time)
        # Move to that action or simulation end
        self.current_time = new_current_time
        for node in self.nodes.values():
            node.update_time(self.current_time)
        # Select nodes to be updated now
        end_action_nodes: list[Node[I, NodeMetrics]] = []
        for node in self.nodes.values():
            if abs(self.current_time - node.next_time) <= TIME_EPS:
                end_action_nodes.append(node)
        # Run actions
        for node in end_action_nodes:
            node.end_action()
            self._after_node_end_action_hook(node)
        self.collect_items()

    def collect_items(self) -> None:
        for node in self.nodes.values():
            for item in node.current_items:
                self.metrics.items.add(item)

    def _before_time_update_hook(self, time: float) -> None:
        self.metrics.passed_time += time - self.current_time

    def _after_node_end_action_hook(self, node: Node[I, NodeMetrics]) -> None:
        if isinstance(node, (BaseFactoryNode, QueueingNode)):
            self.metrics.num_events += 1
