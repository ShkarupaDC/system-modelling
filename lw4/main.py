import itertools
import math
import random
from functools import partial
import time
from pathlib import Path
from dataclasses import dataclass, field

from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from qnet.common import Item, Queue
from qnet.node import Node, NodeMetrics
from qnet.factory import FactoryNode
from qnet.queueing import Task, QueueingNode, QueueingMetrics, ChannelPool
from qnet.transition import ProbaTransitionNode
from qnet.logger import CLILogger
from qnet.model import Model, ModelMetrics, Nodes, Verbosity, Evaluation

ELEMENTARY_OPERATION_TIME = 1e-6  # in seconds


@dataclass(eq=False)
class SystemQueueingMetrics(QueueingMetrics):
    num_tasks_history: list[int] = field(init=False, default_factory=list)


class SystemQueueingNode(QueueingNode[Item, SystemQueueingMetrics]):

    def _before_add_task_hook(self, _: Task[Item]) -> None:
        self.metrics.num_tasks_history.append(self.num_tasks)


def create_model(num_nodes: int, factory_time: float, queueing_time: float,
                 prev_proba: float) -> Model[Item, ModelMetrics[Item]]:
    num_digits = len(str(2 * num_nodes))
    factory = FactoryNode[NodeMetrics](name=f'{1:0{num_digits}d}_factory',
                                       metrics=NodeMetrics(),
                                       delay_fn=partial(random.expovariate, lambd=1.0 / factory_time))
    prev_node: Node[Item, NodeMetrics] = factory

    node_idx = 2
    for idx in range(num_nodes):
        next_node = SystemQueueingNode(name=f'{node_idx:0{num_digits}d}._queueing',
                                       queue=Queue[Item](),
                                       channel_pool=ChannelPool[Item](max_channels=1),
                                       metrics=SystemQueueingMetrics(),
                                       delay_fn=partial(random.expovariate, lambd=1.0 / queueing_time))
        node_idx += 1
        if idx >= 1:
            node = ProbaTransitionNode[Item, NodeMetrics](name=f'{node_idx:0{num_digits}d}_previous_vs_next',
                                                          metrics=NodeMetrics())
            node_idx += 1
            node.add_next_node(prev_node.prev_node, proba=prev_proba)
            node.add_next_node(next_node, proba=1.0 - prev_proba)
            prev_node.set_next_node(node)
        else:
            prev_node.set_next_node(next_node)
        prev_node = next_node

    def num_elementary_operations(model: Model[Item, ModelMetrics[Item]]) -> float:
        num_tasks_history = itertools.chain.from_iterable(node.metrics.num_tasks_history
                                                          for node in model.nodes.values()
                                                          if isinstance(node, SystemQueueingNode))
        num_insert_operations = [
            num_tasks if num_tasks <= 1 else math.log2(num_tasks) for num_tasks in num_tasks_history
        ]
        mean_num_insert_operations = sum(num_insert_operations) / len(num_insert_operations)
        return 2 * (1 + mean_num_insert_operations)

    model = Model(nodes=Nodes[Item].from_node_tree_root(factory),
                  logger=CLILogger[Item](),
                  metrics=ModelMetrics[Item](),
                  evaluations=[Evaluation[float](name='num_elementary_operations', evaluate=num_elementary_operations)])
    return model


def run_simulation(model: Model[Item, ModelMetrics[Item]], simulation_time: float) -> tuple[float, float]:
    start_time = time.perf_counter()
    model.simulate(end_time=simulation_time, verbosity=Verbosity.NONE)
    end_time = time.perf_counter()
    measured_time = end_time - start_time

    num_elem_operations: float = model.evaluation_reports[0].result
    predicted_time = model.model_metrics.mean_event_intensity * model.model_metrics.num_events * num_elem_operations * ELEMENTARY_OPERATION_TIME
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
    save_path = Path('/tmp/time_complexity.png')
    num_nodes = 20
    factory_time = 0.5
    queueing_time = 0.2
    prev_proba = 0.0
    simulation_times = [1e3, 2e3, 3e3, 4e3, 5e3, 6e3, 7e3, 8e3, 9e3, 1e4]

    # Time complexity estimation
    model = create_model(num_nodes=num_nodes,
                         factory_time=factory_time,
                         queueing_time=queueing_time,
                         prev_proba=prev_proba)

    measured_times, predicted_times = [], []

    for simulation_time in tqdm(simulation_times, desc='Simulations'):
        measured_time, predicted_time = run_simulation(model=model, simulation_time=simulation_time)
        model.reset()
        measured_times.append(measured_time)
        predicted_times.append(predicted_time)

    figure = get_time_complexity_plot(simulation_times, measured_times, predicted_times)
    figure.savefig(save_path, dpi=300)
