from typing import Any

from ..lib.base import DelayFn
from ..lib.queueing import Queue, QueueingNode

from .base import HospitalItem, SickType


class AdmissionQueue(Queue[HospitalItem]):

    def pop(self) -> HospitalItem:
        for idx, value in enumerate(self.queue):
            if value.sick_type != SickType.FIRST:
                continue
            self.queue.rotate(-idx)
            item = super().pop()
            self.queue.rotate(idx)
            return item
        return super().pop()


class AdmissionNode(QueueingNode[HospitalItem]):

    def __init__(self, get_delays: dict[SickType, DelayFn], **kwargs: Any) -> None:
        super().__init__(get_delay=lambda item: get_delays[item.sick_type](), **kwargs)
