import random
import itertools
from functools import partial
from typing import Iterable, Any

from qnet.common import Item, Queue
from qnet.node import NM, Node, NodeMetrics
from qnet.factory import FactoryNode
from qnet.queueing import QueueingNode, QueueingMetrics, ChannelPool
from qnet.logger import CLILogger
from qnet.model import Model, Nodes, ModelMetrics

ConcreteQueueingNode = QueueingNode[Item, QueueingMetrics]


class BankFactoryNode(FactoryNode[NM]):

    def __init__(self, max_num_in_bank: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_num_in_bank = max_num_in_bank
        self.operator: ConcreteQueueingNode = None
        self.cachier: ConcreteQueueingNode = None

    @property
    def connected_nodes(self) -> Iterable['Node[Item, NodeMetrics]']:
        return itertools.chain(super().connected_nodes, (self.operator, self.cachier))

    @property
    def num_in_bank(self) -> float:
        return self.operator.queuelen + self.cachier.queuelen + self.cachier.num_tasks + self.operator.num_tasks

    def set_bank_nodes(self, operator: ConcreteQueueingNode, cachier: ConcreteQueueingNode) -> None:
        self.operator = operator
        self.cachier = cachier

    def end_action(self) -> Item:
        self.item = self._get_next_item()
        self.next_time = self._predict_next_time()
        if self.num_in_bank < self.max_num_in_bank:
            return self._end_action(self.item)
        self.next_node, next_node = None, self.next_node
        out_item = self._end_action(self.item)
        self.next_node = next_node
        return out_item


def run_simulation() -> None:
    factory = BankFactoryNode[NodeMetrics](name='1_factory',
                                           max_num_in_bank=10,
                                           metrics=NodeMetrics(),
                                           delay_fn=partial(random.expovariate, lambd=1.0 / 3.0))
    operator = QueueingNode[Item, QueueingMetrics](name='2_operator',
                                                   queue=Queue[Item](),
                                                   metrics=QueueingMetrics(),
                                                   channel_pool=ChannelPool[Item](max_channels=1),
                                                   delay_fn=partial(random.uniform, a=1, b=5))
    cachier = QueueingNode[Item, QueueingMetrics](name='3_cachier',
                                                  queue=Queue[Item](),
                                                  metrics=QueueingMetrics(),
                                                  channel_pool=ChannelPool[Item](max_channels=1),
                                                  delay_fn=partial(random.uniform, a=2, b=4))

    factory.set_bank_nodes(operator=operator, cachier=cachier)
    factory.set_next_node(operator)
    operator.set_next_node(cachier)

    model = Model(nodes=Nodes[Item].from_node_tree_root(factory),
                  logger=CLILogger[Item](),
                  metrics=ModelMetrics[Item]())
    model.simulate(end_time=1000)  # verbosity=Verbosity.METRICS | Verbosity.STATE


if __name__ == '__main__':
    run_simulation()
