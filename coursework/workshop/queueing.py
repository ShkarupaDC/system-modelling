from typing import Any

from qnet.queueing import QueueingNode

from .base import CarUnit


class RepairQueueingNode(QueueingNode[CarUnit]):

    def _predict_item_time(self, **kwargs: Any) -> float:
        item: CarUnit = kwargs['item']
        return self.current_time + item.repair_time

    def _item_in_hook(self, item: CarUnit) -> None:
        super()._item_in_hook(item)
        item.repair_time = self._get_delay(item=item)
