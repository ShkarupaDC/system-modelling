from typing import Any

from qnet.common import ActionType
from qnet.queueing import QM, QueueingNode, Task

from .common import CarUnit


class RepairQueueingNode(QueueingNode[CarUnit, QM]):

    def _predict_item_time(self, **kwargs: Any) -> float:
        item: CarUnit = kwargs['item']
        return self.current_time + item.repair_time

    def _item_in_hook(self, item: CarUnit) -> None:
        super()._item_in_hook(item)
        item.repair_time = self._get_delay(item=item)

    def _item_out_hook(self, item: CarUnit) -> None:
        super()._item_out_hook(item)
        item.num_repairs += 1
        item.repair_time = 0

    def _before_add_task_hook(self, task: Task[CarUnit]) -> None:
        item = task.item
        if not item.history:
            input_time = item.created_time
        else:
            action = item.history[-1]
            assert action.action_type == ActionType.IN and isinstance(action.node,
                                                                      RepairQueueingNode), 'Invalid history'
            input_time = action.time
        item.repair_wait_time += self.current_time - input_time
