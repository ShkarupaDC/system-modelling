import random
from functools import partial

from src.bank import BankQueueingNode, BankQueueingMetrics, BankTransitionNode

from qnet.common import Item, Queue
from qnet.node import NodeMetrics
from qnet.queueing import Task, ChannelPool
from qnet.factory import FactoryNode
from qnet.logger import CLILogger
from qnet.model import Model, ModelMetrics, Nodes, Evaluation, Verbosity


def run_simulation() -> None:
    incoming_cars = FactoryNode[NodeMetrics](name='1_incoming_cars',
                                             metrics=NodeMetrics(),
                                             delay_fn=partial(random.expovariate, lambd=1.0 / 0.5))
    transition = BankTransitionNode[Item, NodeMetrics](name='2_first_vs_second', metrics=NodeMetrics())
    checkout1 = BankQueueingNode[Item](name='3_first_checkout',
                                       min_queuelen_diff=2,
                                       queue=Queue(maxlen=3),
                                       metrics=BankQueueingMetrics(),
                                       channel_pool=ChannelPool[Item](max_channels=1),
                                       delay_fn=partial(random.expovariate, lambd=1.0 / 0.3))
    checkout2 = BankQueueingNode[Item](name='4_second_checkout',
                                       min_queuelen_diff=2,
                                       queue=Queue(maxlen=3),
                                       metrics=BankQueueingMetrics(),
                                       channel_pool=ChannelPool[Item](max_channels=1),
                                       delay_fn=partial(random.expovariate, lambd=1.0 / 0.3))

    incoming_cars.set_next_node(transition)
    transition.set_next_nodes(first=checkout1, second=checkout2)
    checkout1.set_neighbor(checkout2)

    # Initial conditions
    checkout1.add_task(Task[Item](item=Item(id=incoming_cars.next_id, created_time=0.0),
                                  next_time=random.normalvariate(mu=1.0, sigma=0.3)))
    checkout2.add_task(Task[Item](item=Item(id=incoming_cars.next_id, created_time=0.0),
                                  next_time=random.normalvariate(mu=1.0, sigma=0.3)))
    for _ in range(2):
        checkout1.queue.push(Item(id=incoming_cars.next_id, created_time=0.0))
    for _ in range(2):
        checkout2.queue.push(Item(id=incoming_cars.next_id, created_time=0.0))
    incoming_cars.next_time = 0.1

    def total_failure_proba(_: Model[Item, ModelMetrics]) -> float:
        metrics1 = checkout1.metrics
        metrics2 = checkout2.metrics
        return (metrics1.num_failures + metrics2.num_failures) / max(metrics1.num_in + metrics2.num_in, 1)

    def num_switched_checkout(_: Model[Item, ModelMetrics]) -> int:
        return checkout1.metrics.num_from_neighbor + checkout2.metrics.num_from_neighbor

    def mean_cars_in_bank(_: Model[Item, ModelMetrics]) -> float:
        metrics1 = checkout1.metrics
        metrics2 = checkout2.metrics
        return metrics1.mean_channels_load + metrics1.mean_queuelen + metrics2.mean_channels_load + metrics2.mean_queuelen

    model = Model(nodes=Nodes[Item].from_node_tree_root(incoming_cars),
                  evaluations=[
                      Evaluation[float](name='total_failure_proba', evaluate=total_failure_proba),
                      Evaluation[float](name='mean_cars_in_bank', evaluate=mean_cars_in_bank),
                      Evaluation[int](name='num_switched_checkout', evaluate=num_switched_checkout),
                  ],
                  metrics=ModelMetrics[Item](),
                  logger=CLILogger[Item]())
    model.simulate(end_time=10000, verbosity=Verbosity.METRICS)


if __name__ == '__main__':
    run_simulation()
