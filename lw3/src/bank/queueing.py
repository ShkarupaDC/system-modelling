from dataclasses import dataclass, field
from typing import Any

from qnet.common import I
from qnet.queueing import QueueingNode, QueueingMetrics


@dataclass(eq=False)
class BankQueueingMetrics(QueueingMetrics):
    num_from_neighbor: int = field(init=False, default=0)


class BankQueueingNode(QueueingNode[I, BankQueueingMetrics]):

    def __init__(self, min_queuelen_diff: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.min_queuelen_diff = min_queuelen_diff
        self.neighbor: BankQueueingNode[I] = None

    def set_neighbor(self, node: 'BankQueueingNode[I]') -> None:
        self.neighbor = node
        node.neighbor = self

    def end_action(self) -> None:
        item = super().end_action()
        while self.neighbor.queuelen - self.queuelen >= self.min_queuelen_diff:
            last_item = self.neighbor.queue.pop()
            self.neighbor._item_in_hook(last_item)
            self.queue.push(last_item)
            self.metrics.num_from_neighbor += 1
        return item
