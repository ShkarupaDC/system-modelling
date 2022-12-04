import random
from functools import partial
from typing import Union

import numpy as np
import numpy.typing as npt

from workshop import (CarUnit, CarUnitFactoryNode, CarUnitModelMetrics, RepairQueueingNode, AfterControlTransitionNode,
                      WorkshopCLILogger)

from qnet.common import PriorityQueue, Queue
from qnet.dist import erlang
from qnet.node import NodeMetrics
from qnet.model import Evaluation, Model, Nodes, Verbosity
from qnet.queueing import Task, ChannelPool, QueueingNode, QueueingMetrics


def _first_repair_priority_fn(car_unit: CarUnit) -> float:
    return car_unit.repair_time


def _second_repair_priority_fn(car_unit: CarUnit) -> float:
    return float(car_unit.num_repairs < 1)


def _first_to_dict(self: CarUnit) -> str:
    item_dict = super(CarUnit, self).to_dict()
    item_dict['repair_time'] = self.repair_time
    return item_dict


def _second_to_dict(self: CarUnit) -> str:
    item_dict = _first_to_dict(self)
    item_dict.update({'num_repairs': self.num_repairs, 'time_in_system': self.time_in_system})
    return item_dict


def get_simulation_model(factory_delay_mean: float = 10.25,
                         first_repair_priority: bool = True,
                         repair_delay_mean: float = 22.0,
                         repair_delay_var: float = 242.0,
                         repair_max_channels: int = 3,
                         control_delay: float = 6.0,
                         control_max_channels: int = 1,
                         revision_proba=0.15) -> Model[CarUnit, CarUnitModelMetrics]:
    # Dispatch simulation parameters
    if first_repair_priority:
        repair_queue = PriorityQueue[CarUnit](priority_fn=_first_repair_priority_fn, fifo=True)
        to_dict = _first_to_dict
    else:
        repair_queue = PriorityQueue[CarUnit](priority_fn=_second_repair_priority_fn)
        to_dict = _second_to_dict
    setattr(CarUnit, 'to_dict', to_dict)

    repair_delay_lambd = repair_delay_mean / repair_delay_var
    repair_delay_k = int(repair_delay_lambd * repair_delay_mean)

    # Model nodes and transitions
    car_units = CarUnitFactoryNode[NodeMetrics](name='1_car_unit_factory',
                                                metrics=NodeMetrics(),
                                                delay_fn=partial(random.expovariate, lambd=1.0 / factory_delay_mean))
    repair = RepairQueueingNode[QueueingMetrics](name='2_repair_shop',
                                                 queue=repair_queue,
                                                 metrics=QueueingMetrics(),
                                                 channel_pool=ChannelPool(repair_max_channels),
                                                 delay_fn=partial(erlang, lambd=repair_delay_lambd, k=repair_delay_k))
    control = QueueingNode[CarUnit, QueueingMetrics](name='3_control_shop',
                                                     queue=Queue(),
                                                     metrics=QueueingMetrics(),
                                                     channel_pool=ChannelPool(control_max_channels),
                                                     delay_fn=lambda: control_delay)
    after_control = AfterControlTransitionNode[NodeMetrics](name='4_repair_shop_vs_release', metrics=NodeMetrics())

    # Connections
    car_units.set_next_node(repair)
    repair.set_next_node(control)
    control.set_next_node(after_control)
    after_control.add_next_node(repair, proba=revision_proba)
    after_control.add_next_node(None, proba=after_control.rest_proba)

    # Initial condition
    # repair.add_task(Task(CarUnit(id=car_units.next_id, created_time=0), next_time=1.0))
    repair.add_task(Task(CarUnit(id=car_units.next_id, created_time=0), next_time=1.5))
    car_units.next_time = 0

    def mean_units_in_system(_: Model) -> float:
        return (repair.metrics.mean_queuelen + repair.metrics.mean_channels_load + control.metrics.mean_queuelen +
                control.metrics.mean_channels_load)

    model = Model(nodes=Nodes[CarUnit].from_node_tree_root(car_units),
                  metrics=CarUnitModelMetrics(),
                  logger=WorkshopCLILogger(),
                  evaluations=[Evaluation[float](name='mean_units_in_system', evaluate=mean_units_in_system)])
    return model


def collect_model_metrics(model: Union[bytes, Model[CarUnit, CarUnitModelMetrics]], metric_name: str, start_time: float,
                          end_time: float, collect_step_time: float) -> npt.NDArray[np.float32]:
    if isinstance(model, bytes):
        model = Model[CarUnit, CarUnitModelMetrics].loads(model)

    while model.step(start_time):
        pass
    model.reset_metrics()

    num_steps = (end_time - start_time) // collect_step_time
    metrics = np.empty(num_steps)
    next_time, step = start_time + collect_step_time, 0
    while True:
        if model.next_time < next_time:
            if not model.step(end_time):
                break
        else:
            model.goto(next_time, end_time)
            metrics[step] = getattr(model.model_metrics, metric_name)
            step += 1
            next_time += collect_step_time
    return metrics


def run_simulation(model: Union[bytes, Model[CarUnit, CarUnitModelMetrics]], metric_name: str,
                   simulation_time: float) -> float:
    if isinstance(model, bytes):
        model = Model[CarUnit, CarUnitModelMetrics].loads(model)

    model.simulate(simulation_time, verbosity=Verbosity.NONE)
    return getattr(model.model_metrics, metric_name)


if __name__ == '__main__':
    model = get_simulation_model(factory_delay_mean=10.25,
                                 first_repair_priority=False,
                                 repair_delay_mean=22.0,
                                 repair_delay_var=242.0,
                                 repair_max_channels=3,
                                 control_delay=6.0,
                                 control_max_channels=1,
                                 revision_proba=0.15)
    model.simulate(end_time=10000, verbosity=Verbosity.METRICS)  # Verbosity.STATE | Verbosity.METRICS
