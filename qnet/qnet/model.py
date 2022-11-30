from enum import Flag
from dataclasses import dataclass, field
from typing import Callable, Generic, Optional, Type, TypeVar

from qnet.common import INF_TIME, TIME_EPS, T
from qnet.base import Node, Metrics, NodeMetrics
from qnet.factory import BaseFactoryNode
from qnet.queueing import QueueingNode
from qnet.logger import BaseLogger, CLILogger

M = TypeVar('M', bound='Model')


class Nodes(dict[str, Node[T]]):

    @staticmethod
    def from_node_tree_root(node_tree_root: Node[T]) -> 'Nodes[T]':
        nodes = Nodes[T]()

        def process_node(parent: Optional[Node[T]]) -> None:
            if parent.name in nodes and nodes[parent.name] != parent:
                raise ValueError('Nodes must have different names')
            nodes[parent.name] = parent
            for node in parent.connected_nodes:
                if node is not None and node.name not in nodes:
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
    evaluate: Callable[['Model'], T]

    def __call__(self, model: 'Model') -> EvaluationReport[T]:
        return EvaluationReport[T](name=self.name, result=self.evaluate(model))


@dataclass(eq=False)
class ModelMetrics(Metrics[M]):
    num_events: int = field(init=False, default=0)

    @property
    def mean_event_intensity(self) -> float:
        return self.num_events / max(self.passed_time, TIME_EPS)


class Verbosity(Flag):
    NONE = 0b00
    STATE = 0b01
    METRICS = 0b10


class Model(Generic[T]):

    def __init__(
            self,
            nodes: Nodes,
            metrics_type: Type[ModelMetrics] = ModelMetrics,
            evaluations: Optional[list[Evaluation]] = None,
            logger: BaseLogger = CLILogger(),
    ) -> None:
        self.nodes = nodes
        self.logger = logger
        self.metrics = metrics_type[Model[T]](self)
        self.evaluations = [] if evaluations is None else evaluations
        self.current_time = 0
        self.updated_nodes: list[Node[T]] = []

    @property
    def next_time(self) -> float:
        return min(INF_TIME, *(node.next_time for node in self.nodes.values()))

    @property
    def model_metrics(self) -> ModelMetrics['Model']:
        return self.metrics

    @property
    def nodes_metrics(self) -> list[NodeMetrics[Node[T]]]:
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
                self.logger.nodes_states(self.current_time, list(self.nodes.values()), self.updated_nodes)
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
        self.updated_nodes.clear()
        for node in self.nodes.values():
            if abs(new_current_time - node.next_time) <= TIME_EPS:
                self.updated_nodes.append(node)
        # Run actions
        for node in self.updated_nodes:
            node.end_action()
            self._after_node_end_action_hook(node)

    def _before_time_update_hook(self, time: float) -> None:
        self.metrics.passed_time += time - self.current_time

    def _after_node_end_action_hook(self, node: Node[T]) -> None:
        if isinstance(node, (BaseFactoryNode, QueueingNode)):
            self.metrics.num_events += 1
