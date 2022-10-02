import random
from typing import Any

from ..lib.factory import BaseFactoryNode

from .base import HospitalItem, SickType


class HospitalFactoryNode(BaseFactoryNode[HospitalItem]):

    def __init__(self, probas: dict[SickType, float], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.probas = probas

    def end_action(self) -> HospitalItem:
        sick_type = self._get_next_type()
        item = HospitalItem(id=self.stats.num_out, sick_type=sick_type)
        return self._end_action_hook(item)

    def _get_next_type(self) -> SickType:
        return random.choices(self.probas.keys(), self.probas.values(), k=1)[0]
