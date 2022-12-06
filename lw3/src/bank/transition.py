import itertools
from typing import Iterable, Optional, Any

from qnet.common import I
from qnet.node import NM, Node, NodeMetrics
from qnet.transition import BaseTransitionNode

from .queueing import BankQueueingNode


class BankTransitionNode(BaseTransitionNode[I, NM]):

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.first: BankQueueingNode[I] = None
        self.second: BankQueueingNode[I] = None

    @property
    def connected_nodes(self) -> Iterable['Node[I, NodeMetrics]']:
        return itertools.chain((self.first, self.second), super().connected_nodes)

    def set_next_nodes(self, first: BankQueueingNode[I], second: BankQueueingNode[I]) -> None:
        self.first = first
        self.second = second

    def to_dict(self) -> dict[str, Any]:
        return {
            'next_node': self.next_node.name if self.next_node else None,
            'first_queue_size': self.first.queuelen,
            'second_queue_size': self.second.queuelen
        }

    def _get_next_node(self, _: I) -> Optional[Node[I, NodeMetrics]]:
        return self.first if self.first.queuelen <= self.second.queuelen else self.second
