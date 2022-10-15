from lib.queueing import Queue

from .base import HospitalItem, SickType


class EmergencyQueue(Queue[HospitalItem]):

    def pop(self) -> HospitalItem:
        for idx, item in enumerate(self.queue):
            if item.sick_type == SickType.FIRST or item.as_first_sick:
                self.queue.rotate(-idx)
                first_item = super().pop()
                self.queue.rotate(idx)
                return first_item
        return super().pop()
