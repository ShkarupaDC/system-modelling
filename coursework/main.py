import random
from functools import partial

from workshop import (CarUnit, CarUnitFactoryNode, CarUnitModelMetrics, RepairQueueingNode, AfterControlTransitionNode,
                      WorkshopCLILogger)

from qnet.common import PriorityQueue, Queue, ActionType, ActionRecord
from qnet.dist import erlang
from qnet.node import NodeMetrics
from qnet.model import Evaluation, Model, Nodes, Verbosity
from qnet.queueing import Channel, QueueingNode, QueueingMetrics


def _first_repair_priority_fn(car_unit: CarUnit) -> float:
    return car_unit.repair_time


def _second_repair_priority_fn(car_unit: CarUnit) -> float:
    return float(not car_unit.returned)


def _second_repair_priority__lt__(self: CarUnit, other: 'CarUnit') -> bool:
    assert self.returned == other.returned, 'Invalid priority function'

    if self.returned and other.returned:
        return self.time_in_system > other.time_in_system

    def assert_action(action: ActionRecord) -> None:
        assert action.action_type == ActionType.IN and isinstance(action.node, RepairQueueingNode), 'Invalid history'

    self_action, other_action = self.history[-1], other.history[-1]
    assert_action(self_action)
    assert_action(other_action)
    return self_action.time < other_action.time


def _second_repair_priority__repr__(self: CarUnit) -> str:
    return f'CarUnit(id={self.id}, returned={self.returned}, time_in_system={self.time_in_system:.3f})'


def get_simulation_model(first_repair_priority: bool) -> Model[CarUnit, CarUnitModelMetrics]:
    # Dispatch simulation rules
    if first_repair_priority:
        repair_queue = PriorityQueue[CarUnit](priority_fn=_first_repair_priority_fn, fifo=True)
    else:
        setattr(CarUnit, '__lt__', _second_repair_priority__lt__)
        repair_queue = PriorityQueue[CarUnit](priority_fn=_second_repair_priority_fn)
        setattr(CarUnit, '__repr__', _second_repair_priority__repr__)
    # Model nodes and transitions
    car_units = CarUnitFactoryNode[NodeMetrics](name='1_car_unit_factory',
                                                metrics=NodeMetrics(),
                                                delay_fn=partial(random.expovariate, lambd=1.0 / 10.25))
    repair = RepairQueueingNode[QueueingMetrics](name='2_repair_shop',
                                                 queue=repair_queue,
                                                 metrics=QueueingMetrics(),
                                                 max_channels=3,
                                                 delay_fn=partial(erlang, lambd=22 / 242, k=int(22 * 22 / 242)))
    control = QueueingNode[CarUnit, QueueingMetrics](name='3_control_shop',
                                                     queue=Queue(),
                                                     metrics=QueueingMetrics(),
                                                     max_channels=1,
                                                     delay_fn=lambda: 6)
    after_control = AfterControlTransitionNode[NodeMetrics](name='4_repair_shop_vs_release', metrics=NodeMetrics())

    # Connections
    car_units.set_next_node(repair)
    repair.set_next_node(control)
    control.set_next_node(after_control)
    after_control.add_next_node(repair, proba=0.15)

    # Initial condition
    repair.add_channel(Channel(CarUnit(id=car_units.next_id, created_time=0), next_time=1.0))
    repair.add_channel(Channel(CarUnit(id=car_units.next_id, created_time=0), next_time=1.5))
    car_units.next_time = 0

    def mean_units_in_system(_: Model) -> float:
        return (repair.metrics.mean_queuelen + repair.metrics.mean_busy_channels + control.metrics.mean_queuelen +
                control.metrics.mean_busy_channels)

    model = Model(nodes=Nodes[CarUnit].from_node_tree_root(car_units),
                  metrics=CarUnitModelMetrics(),
                  logger=WorkshopCLILogger(),
                  evaluations=[Evaluation[float](name='mean_units_in_system', evaluate=mean_units_in_system)])
    return model


if __name__ == '__main__':
    model = get_simulation_model(first_repair_priority=True)
    model.simulate(end_time=10000, verbosity=Verbosity.METRICS)  # Verbosity.STATE | Verbosity.METRICS
