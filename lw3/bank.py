import random
from functools import partial

from src.lib.base import Item
from src.lib.queueing import Queue
from src.lib.factory import FactoryNode
from src.lib.model import Model

from src.bank import BankQueueingNode, BankTransitionNode, BankLogger


def run_simulation() -> None:
    incoming_cars = FactoryNode(delay_fn=partial(random.expovariate, lambd=1.0 / 0.5))
    first_checkout = BankQueueingNode[Item](min_diff=2,
                                            queue=Queue(maxlen=3),
                                            max_handlers=1,
                                            delay_fn=partial(random.expovariate, lambd=1.0 / 0.3))
    second_checkout = BankQueueingNode[Item](min_diff=2,
                                             queue=Queue(maxlen=3),
                                             max_handlers=1,
                                             delay_fn=partial(random.expovariate, lambd=1.0 / 0.3))
    first_checkout.set_neighbor(second_checkout)
    transition = BankTransitionNode[Item](first=first_checkout, second=second_checkout)
    incoming_cars.set_next_node(transition)
    model = Model.from_factory(incoming_cars, logger=BankLogger())
    model.simulate(end_time=10, verbose=True)


if __name__ == '__main__':
    run_simulation()
