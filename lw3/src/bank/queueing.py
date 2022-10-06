from dataclasses import dataclass, field
from typing import Type, TypeVar, Any

from ..lib.common import T
from ..lib.queueing import QueueingNode, QueueingMetrics

BQ = TypeVar('BQ', bound='BankQueueingNode')


@dataclass(eq=False)
class BankQueueingMetrics(QueueingMetrics[BQ]):
    num_from_neighbor: int = field(init=False, default=0)


class BankQueueingNode(QueueingNode[T]):

    def __init__(self,
                 min_diff: int,
                 metrics_type: Type[BankQueueingMetrics[BQ]] = BankQueueingMetrics,
                 **kwargs: Any) -> None:
        self.metrics: BankQueueingMetrics = None
        super().__init__(metrics_type=metrics_type, **kwargs)

        self.min_diff = min_diff  # in queues' lengths
        self.neighbor: BankQueueingNode[T] = None

    def set_neighbor(self, node: 'BankQueueingNode[T]') -> None:
        self.neighbor = node
        node.neighbor = self

    def end_action(self) -> None:
        item = super().end_action()
        while self.neighbor.queuelen - self.queuelen >= self.min_diff:
            last_item = self.neighbor.queue.pop()
            self.queue.push(last_item)
            self.neighbor._in_metrics_hook()
            self.metrics.num_from_neighbor += 1
        return item
