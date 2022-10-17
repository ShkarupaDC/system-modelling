import random
from functools import partial

from lib.common import erlang
from lib.model import Evaluation, Model
from lib.queueing import Channel, QueueingNode, PriorityQueue
from lib.logger import _format_float

from src.workshop import CarUnit, CarUnitFactory, RepairQueueingNode, AfterControlTransition, WorkshopLogger


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
    repair.channels.push(Channel(CarUnit(id=car_units.next_id), next_time=1.0))
    repair.channels.push(Channel(CarUnit(id=car_units.next_id), next_time=1.5))
    car_units.next_time = 0

    def mean_units_in_system(_: Model) -> float:
        return (repair.metrics.mean_queuelen + repair.metrics.mean_busy_channels + control.metrics.mean_queuelen +
                control.metrics.mean_busy_channels)

    model = Model.from_factory(car_units,
                               logger=WorkshopLogger(),
                               evaluations=[
                                   Evaluation[float](name='Mean units in system',
                                                     evaluate=mean_units_in_system,
                                                     serialize=_format_float)
                               ])
    model.simulate(end_time=1000)


if __name__ == '__main__':
    run_simulation()
