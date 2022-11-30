import random
from functools import partial

from src.bank import BankQueueingNode, BankTransitionNode, BankCLILogger

from qnet.base import Item
from qnet.queueing import Channel, Queue
from qnet.factory import FactoryNode
from qnet.model import Model, Nodes, Evaluation, Verbosity


def run_simulation() -> None:
    incoming_cars = FactoryNode(name='1. Incoming Cars', delay_fn=partial(random.expovariate, lambd=1.0 / 0.5))
    checkout1 = BankQueueingNode[Item](name='3. First checkout',
                                       min_queuelen_diff=2,
                                       queue=Queue(maxlen=3),
                                       max_channels=1,
                                       delay_fn=partial(random.expovariate, lambd=1.0 / 0.3))
    checkout2 = BankQueueingNode[Item](name='4. Second checkout',
                                       min_queuelen_diff=2,
                                       queue=Queue(maxlen=3),
                                       max_channels=1,
                                       delay_fn=partial(random.expovariate, lambd=1.0 / 0.3))
    checkout1.set_neighbor(checkout2)
    transition = BankTransitionNode[Item](name='2. First vs Second', first=checkout1, second=checkout2)
    incoming_cars.set_next_node(transition)

    # Initial conditions
    checkout1.add_channel(
        Channel(item=Item(id=incoming_cars.next_id), next_time=random.normalvariate(mu=1.0, sigma=0.3)))
    checkout2.add_channel(
        Channel(item=Item(id=incoming_cars.next_id), next_time=random.normalvariate(mu=1.0, sigma=0.3)))
    for _ in range(2):
        checkout1.queue.push(Item(id=incoming_cars.next_id))
    for _ in range(2):
        checkout2.queue.push(Item(id=incoming_cars.next_id))
    incoming_cars.next_time = 0.1

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

    model = Model(nodes=Nodes[Item].from_node_tree_root(incoming_cars),
                  evaluations=[
                      Evaluation[float](name='total_failure_proba', evaluate=total_failure_proba),
                      Evaluation[float](name='mean_cars_in_bank', evaluate=mean_cars_in_bank),
                      Evaluation[int](name='num_switched_checkout', evaluate=num_switched_checkout),
                  ],
                  logger=BankCLILogger())
    model.simulate(end_time=10000, verbosity=Verbosity.METRICS)


if __name__ == '__main__':
    run_simulation()
