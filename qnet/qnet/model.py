from enum import Flag, auto
from dataclasses import dataclass, field
from typing import Callable, Generic, Optional, Type, TypeVar, Any

from qnet.common import INF_TIME, TIME_EPS, T
from qnet.base import Node, Metrics, NodeMetrics
from qnet.factory import BaseFactoryNode
from qnet.queueing import QueueingNode
from qnet.logger import BaseLogger, Logger

M = TypeVar('M', bound='Model')


@dataclass(eq=False)
class EvaluationReport(Generic[T]):
    name: str
    result: T
    serialize: Callable[[T], str]

    @property
    def report(self) -> str:
        return self.serialize(self.result)


@dataclass(eq=False)
class Evaluation(Generic[T]):
    name: str
    evaluate: Callable[['Model'], T]
    serialize: Callable[[T], str] = str

    def __call__(self, model: 'Model') -> EvaluationReport[T]:
        return EvaluationReport[T](name=self.name, result=self.evaluate(model), serialize=self.serialize)


@dataclass(eq=False)
class ModelMetrics(Metrics[M]):
    num_events: int = field(init=False, default=0)

    @property
    def mean_event_intensity(self) -> float:
        return self.num_events / max(self.parent.current_time, TIME_EPS)


class Verbosity(Flag):
    NONE = auto()
    STATE = auto()
    METRICS = auto()


ModellingMetrics = tuple[ModelMetrics, list[EvaluationReport], list[NodeMetrics]]


class Model(Generic[T]):

    def __init__(
            self,
            nodes: list[Node[T]],
            metrics_type: Type[ModelMetrics] = ModelMetrics,
            evaluations: Optional[list[Evaluation]] = None,
            logger: BaseLogger = Logger(),
    ) -> None:
        self.nodes = nodes
        self.logger = logger
        self.metrics = metrics_type[Model[T]](self)
        self.evaluations = [] if evaluations is None else evaluations
        self.current_time = 0

    def simulate(self, end_time: float, verbosity: Verbosity = Verbosity.METRICS) -> ModellingMetrics:
        while self.current_time < end_time:
            # Run simulation step
            updated_nodes = self.step(end_time)
            if updated_nodes is None:
                break
            # Log state
            if Verbosity.STATE in verbosity:
                self.logger.log_state(self.current_time, self.nodes, updated_nodes)
        # Collect metrics
        metrics = self.get_metrics()
        # Log metrics
        if Verbosity.METRICS in verbosity:
            self.logger.log_metrics(*metrics)
        return metrics

    def step(self, end_time: Optional[float] = None) -> Optional[list[Node[T]]]:
        if end_time is not None and self.current_time > end_time:
            return None
        # Find next closest action
        next_time = min(INF_TIME, *(node.next_time for node in self.nodes))
        if end_time is not None and next_time > end_time:
            return None
        # Move to that action
        self.current_time = next_time
        for node in self.nodes:
            node.update_time(self.current_time)
        # Select nodes to be updated now
        updated_nodes: list[Node[T]] = []
        for node in self.nodes:
            if abs(next_time - node.next_time) > TIME_EPS:
                continue
            updated_nodes.append(node)
        # Run actions
        for node in updated_nodes:
            node.end_action()
            if isinstance(node, (BaseFactoryNode, QueueingNode)):
                self.metrics.num_events += 1
        return updated_nodes

    def reset(self) -> None:
        self.current_time = 0
        for node in self.nodes:
            node.reset()
        self.metrics.reset()

    def get_metrics(self) -> ModellingMetrics:
        nodes_metrics = [node.metrics for node in self.nodes]
        evaluation_reports = [evaluation(self) for evaluation in self.evaluations]
        return self.metrics, nodes_metrics, evaluation_reports

    @staticmethod
    def from_factory(factory: Node[T], **kwargs: Any) -> 'Model[T]':
        nodes: set[Node[T]] = set()

        def process_node(parent: Optional[Node[T]]) -> None:
            if parent is None:
                return
            nodes.add(parent)
            for node in parent.connected_nodes:
                if node not in nodes:
                    process_node(node)

        process_node(factory)
        return Model[T](nodes=list(nodes), **kwargs)
