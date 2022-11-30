import random
from functools import partial

from workshop import CarUnit, CarUnitFactory, RepairQueueingNode, AfterControlTransition, WorkshopCLILogger

from qnet.common import erlang
from qnet.model import Evaluation, Model, Nodes
from qnet.queueing import Channel, QueueingNode, PriorityQueue


def run_simulation() -> None:

    def repair_time_priority(car_unit: CarUnit) -> float:
        return car_unit.repair_time

    def compare_priority(_: CarUnit) -> float:  # pylint: disable=unused-variable
        return -1

    # Model nodes and transitions
    car_units = CarUnitFactory(name='1. Car unit factory', delay_fn=partial(random.expovariate, lambd=1.0 / 10.25))
    repair = RepairQueueingNode(name='2. Repair shop',
                                queue=PriorityQueue(priority_fn=repair_time_priority, fifo=True),
                                max_channels=3,
                                delay_fn=partial(erlang, lambd=22 / 242, k=int(22 * 22 / 242)))
    # queue=PriorityQueue(priority_fn=compare_priority)
    control = QueueingNode[CarUnit](name='3. Control shop', max_channels=1, delay_fn=lambda: 6)
    after_control = AfterControlTransition(name='4. Repair shop vs Release')

    # Connections
    car_units.set_next_node(repair)
    repair.set_next_node(control)
    control.set_next_node(after_control)
    after_control.add_next_node(repair, proba=0.15)

    # Initial condition
    repair.add_channel(Channel(CarUnit(id=car_units.next_id), next_time=1.0))
    repair.add_channel(Channel(CarUnit(id=car_units.next_id), next_time=1.5))
    car_units.next_time = 0

    def mean_units_in_system(_: Model) -> float:
        return (repair.metrics.mean_queuelen + repair.metrics.mean_busy_channels + control.metrics.mean_queuelen +
                control.metrics.mean_busy_channels)

    model = Model(nodes=Nodes.from_node_tree_root(car_units),
                  logger=WorkshopCLILogger(),
                  evaluations=[Evaluation[float](name='mean_units_in_system', evaluate=mean_units_in_system)])
    model.simulate(end_time=10000)


if __name__ == '__main__':
    run_simulation()
