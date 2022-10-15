import random
from functools import partial

from lib.base import Item
from lib.queueing import Queue
from lib.factory import FactoryNode
from lib.model import Model, Evaluation
from lib.logger import _format_float

from src.bank import BankQueueingNode, BankTransitionNode, BankLogger


def run_simulation() -> None:
    incoming_cars = FactoryNode(name='1. Incoming Cars', delay_fn=partial(random.expovariate, lambd=1.0 / 0.5))
    checkout1 = BankQueueingNode[Item](name='3. First checkout',
                                       min_diff=2,
                                       queue=Queue(maxlen=3),
                                       max_channels=1,
                                       delay_fn=partial(random.expovariate, lambd=1.0 / 0.3))
    checkout2 = BankQueueingNode[Item](name='4. Second checkout',
                                       min_diff=2,
                                       queue=Queue(maxlen=3),
                                       max_channels=1,
                                       delay_fn=partial(random.expovariate, lambd=1.0 / 0.3))
    checkout1.set_neighbor(checkout2)
    transition = BankTransitionNode[Item](name='2. First vs Second', first=checkout1, second=checkout2)
    incoming_cars.set_next_node(transition)

    def total_failure_proba(_: Model) -> float:
        metrics1 = checkout1.metrics
        metrics2 = checkout2.metrics
        return (metrics1.num_failures + metrics2.num_failures) / max(metrics1.num_in + metrics2.num_in, 1)

    def num_switched_checkout(_: Model) -> int:
        return checkout1.metrics.num_from_neighbor + checkout2.metrics.num_from_neighbor

    def mean_cars_in_bank(_: Model) -> float:
        metrics1 = checkout1.metrics
        metrics2 = checkout2.metrics
        return metrics1.mean_busy_channels + metrics1.mean_queuelen + metrics2.mean_busy_channels + metrics2.mean_queuelen

    model = Model.from_factory(incoming_cars,
                               evaluations=[
                                   Evaluation[float](name='Total failure proba',
                                                     evaluate=total_failure_proba,
                                                     serialize=_format_float),
                                   Evaluation[float](name='Mean number of cars in bank',
                                                     evaluate=mean_cars_in_bank,
                                                     serialize=_format_float),
                                   Evaluation[int](name='Num switched checkout', evaluate=num_switched_checkout)
                               ],
                               logger=BankLogger())
    model.simulate(end_time=10000)


if __name__ == '__main__':
    run_simulation()
