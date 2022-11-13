from typing import Iterable, Optional, Any

from qnet.common import T
from qnet.base import Node
from qnet.transition import BaseTransitionNode

from .queueing import BankQueueingNode


class BankTransitionNode(BaseTransitionNode[T]):

    def __init__(self, first: BankQueueingNode, second: BankQueueingNode, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.first = first
        self.second = second

    @property
    def connected_nodes(self) -> Iterable[Node[T]]:
        return [self.first, self.second]

    def _get_next_node(self, _: T) -> Optional[Node[T]]:
        return self.first if self.first.queuelen <= self.second.queuelen else self.second
