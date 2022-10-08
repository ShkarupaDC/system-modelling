from enum import Flag, auto
from dataclasses import dataclass, field
from typing import Callable, Generic, Optional, Type, Any

from .common import INF_TIME, TIME_EPS, T
from .base import Node, Metrics, NodeMetrics
from .factory import BaseFactoryNode
from .queueing import QueueingNode
from .logger import Logger


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
class ModelMetrics(Metrics[T]):
    num_events: int = field(init=False, default=0)
    simulation_time: float = field(init=False, default=0)

    @property
    def mean_event_intensity(self) -> float:
        return self.num_events / max(self.simulation_time, TIME_EPS)


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
            logger: Logger = Logger(),
    ) -> None:
        self.nodes = nodes
        self.logger = logger
        self.metrics = metrics_type[Model[T]](self)
        self.evaluations = [] if evaluations is None else evaluations

    def simulate(self, end_time: float, verbosity: Verbosity = Verbosity.METRICS) -> ModellingMetrics:
        self.reset()
        current_time = 0
        while current_time < end_time:
            # Find next closest action
            next_time = INF_TIME
            for node in self.nodes:
                if node.next_time < next_time:
                    next_time = node.next_time
            if next_time > end_time:
                break
            # Move to that action
            current_time = next_time
            for node in self.nodes:
                node.update_time(current_time)
            # Run actions
            updated_nodes: list[Node[T]] = []
            for node in self.nodes:
                if abs(next_time - node.next_time) > TIME_EPS:
                    continue
                updated_nodes.append(node)
                node.end_action()
                if isinstance(node, (BaseFactoryNode, QueueingNode)):
                    self.metrics.num_events += 1
            # Log states
            if Verbosity.STATE in verbosity:
                self.logger.log_state(current_time, self.nodes, updated_nodes)
        self.metrics.simulation_time = current_time
        modelling_metrics = self.metrics, [node.metrics for node in self.nodes
                                           ], [evaluation(self) for evaluation in self.evaluations]
        # Log metrics
        if Verbosity.METRICS in verbosity:
            self.logger.log_metrics(*modelling_metrics)
        return modelling_metrics

    def reset(self) -> None:
        for node in self.nodes:
            node.reset()
        self.metrics.reset()

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
