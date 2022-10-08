import itertools
import math
import random
from functools import partial
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Type, Any

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from src.lib.base import Node, Item
from src.lib.factory import FactoryNode
from src.lib.queueing import QueueingNode, QueueingMetrics
from src.lib.transition import ProbaTransitionNode
from src.lib.model import Model, Verbosity, Evaluation
from src.lib.logger import _format_float

ELEMENTARY_OPERATION_TIME = 1e-6  # in seconds


@dataclass(eq=False)
class SystemQueueingMetrics(QueueingMetrics['SystemQueueingNode']):
    num_handlers_history: list[int] = field(init=False, default_factory=list)


class SystemQueueingNode(QueueingNode[Item]):

    def __init__(self, metrics_type: Type[SystemQueueingMetrics] = SystemQueueingMetrics, **kwargs: Any) -> None:
        self.metrics: SystemQueueingMetrics = None
        super().__init__(metrics_type=metrics_type, **kwargs)

    def _before_add_handler_hook(self) -> None:
        self.metrics.num_handlers_history.append(self.num_handlers)


def create_model(num_nodes: int, factory_time: float, queueing_time: float, prev_proba: float) -> Model[Item]:
    num_digits = len(str(2 * num_nodes))
    factory = FactoryNode(name=f'{1:0{num_digits}d}. Factory',
                          delay_fn=partial(random.expovariate, lambd=1.0 / factory_time))
    prev_node: Node[Item] = factory

    node_idx = 0
    for idx in range(num_nodes):
        node = SystemQueueingNode(name=f'{node_idx:0{num_digits}d}. Queueing',
                                  max_handlers=1,
                                  delay_fn=partial(random.expovariate, lambd=1.0 / queueing_time))
        node_idx += 1
        if idx >= 1:
            mext_probas = {prev_node: prev_proba, node: 1.0 - prev_proba}
            next_node = ProbaTransitionNode[Item](name=f'{node_idx:0{num_digits}d}. Previous vs Next',
                                                  nodes_probas=mext_probas)
            node_idx += 1
        else:
            next_node = node
        prev_node.set_next_node(next_node)
        prev_node = node

    def num_elementary_operations(model: Model[Item]) -> float:
        num_handlers_history = itertools.chain.from_iterable(node.metrics.num_handlers_history for node in model.nodes
                                                             if isinstance(node, SystemQueueingNode))
        num_insert_operations = [
            num_handlers if num_handlers <= 1 else math.log2(num_handlers) for num_handlers in num_handlers_history
        ]
        mean_num_insert_operations = sum(num_insert_operations) / len(num_insert_operations)
        return 2 * (1 + mean_num_insert_operations)

    model = Model[Item].from_factory(factory=factory,
                                     evaluations=[
                                         Evaluation[float](name='Num elementary operations',
                                                           evaluate=num_elementary_operations,
                                                           serialize=_format_float)
                                     ])
    return model


def run_simulation(model: Model[Item], simulation_time: float) -> tuple[float, float]:
    start_time = time.perf_counter()
    metrics, _, evaluations = model.simulate(end_time=simulation_time, verbosity=Verbosity.NONE)
    end_time = time.perf_counter()
    measured_time = end_time - start_time

    num_elem_operations: float = evaluations[0].result
    predicted_time = metrics.mean_event_intensity * metrics.num_events * num_elem_operations * ELEMENTARY_OPERATION_TIME
    return measured_time, predicted_time


def get_time_complexity_plot(simulation: list[float], measured: list[float], predicted: list[float]) -> Figure:
    figure, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 10))
    ax.plot(simulation, measured, color='blue', label='measured')
    ax.plot(simulation, predicted, color='red', label='predicted')
    ax.legend()
    ax.grid(True)
    ax.set(xlabel='Simulation time', ylabel='Real Time', title='Time complexity estimation')
    return figure


if __name__ == '__main__':
    # Parameters
    save_path = Path.cwd().joinpath('time_complexity.png')
    num_nodes = 20
    factory_time = 0.5
    queueing_time = 0.2
    prev_proba = 0.0
    simulation_times = [1e3, 2e3, 3e3, 4e3, 5e3, 6e3, 7e3, 8e3, 9e3, 1e4]

    # Time complexity estimation
    measured_times, predicted_times = zip(*[
        run_simulation(model=create_model(
            num_nodes=num_nodes, factory_time=factory_time, queueing_time=queueing_time, prev_proba=prev_proba),
                       simulation_time=simulation_time) for simulation_time in simulation_times
    ])
    figure = get_time_complexity_plot(simulation_times, measured_times, predicted_times)
    figure.savefig(save_path, dpi=300)