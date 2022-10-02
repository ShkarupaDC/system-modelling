from dataclasses import dataclass, field
from typing import Any

from ..lib.common import T
from ..lib.queueing import QueueingNode, QueueingStats


@dataclass(eq=False)
class BankQueueingStats(QueueingStats):
    num_queue_switches: int = field(init=False, default=0)  # incoming


class BankQueueingNode(QueueingNode[T]):

    def __init__(self, min_diff: int, **kwargs: Any) -> None:
        self.stats: BankQueueingStats = None
        super().__init__(stats_type=BankQueueingStats, **kwargs)

        self.min_diff = min_diff  # in queues' lengths
        self.neighbor: BankQueueingNode[T] = None

    def set_neighbor(self, node: 'BankQueueingNode[T]') -> None:
        self.neighbor = node

    def end_action(self) -> None:
        item = super().end_action()
        while self.neighbor.queuelen - self.queuelen >= self.min_diff:
            last_item = self.neighbor.queue.pop()
            self.queue.push(last_item)
            self.stats.num_queue_switches += 1
        return item
