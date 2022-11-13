import random
from functools import partial
from typing import Any

from qnet.base import Item
from qnet.factory import FactoryNode
from qnet.queueing import QueueingNode, Queue
from qnet.model import Model


class BankFactoryNode(FactoryNode):

    def __init__(self, max_num_in_bank: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_num_in_bank = max_num_in_bank
        self.operator: QueueingNode[Item] = None
        self.cachier: QueueingNode[Item] = None

    @property
    def num_in_bank(self) -> float:
        return self.operator.queuelen + self.cachier.queuelen + self.cachier.num_channels + self.operator.num_channels

    def set_bank_nodes(self, operator: QueueingNode[Item], cachier: QueueingNode[Item]) -> None:
        self.operator = operator
        self.cachier = cachier

    # pylint: disable=attribute-defined-outside-init
    def end_action(self) -> Item:
        self.item = self._get_next_item()
        self.metrics.items.append(self.item)
        self.next_time = self._predict_next_time()
        failure = self.num_in_bank > self.max_num_in_bank
        if failure:
            self.next_node, next_node = None, self.next_node
        out_item = self._end_action(self.item)
        if failure:
            self.next_node = next_node
        return out_item


def run_simulation() -> None:
    factory = BankFactoryNode(name='1. Factory',
                              max_num_in_bank=10,
                              delay_fn=partial(random.expovariate, lambd=1.0 / 3.0))
    operator = QueueingNode[Item](name='2. Operator',
                                  queue=Queue(),
                                  max_channels=1,
                                  delay_fn=partial(random.uniform, a=1, b=5))
    cachier = QueueingNode[Item](name='3. Cachier',
                                 queue=Queue(),
                                 max_channels=1,
                                 delay_fn=partial(random.uniform, a=2, b=4))

    factory.set_bank_nodes(operator=operator, cachier=cachier)
    factory.set_next_node(operator)
    operator.set_next_node(cachier)

    model = Model.from_factory(factory)
    model.simulate(end_time=1000)  # verbosity=Verbosity.METRICS | Verbosity.STATE


if __name__ == '__main__':
    run_simulation()
