import random
from typing import Any

from qnet.node import NM
from qnet.factory import BaseFactoryNode

from .common import HospitalItem, SickType


class HospitalFactoryNode(BaseFactoryNode[HospitalItem, NM]):

    def __init__(self, probas: dict[SickType, float], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.sick_types, self.sick_probas = zip(*probas.items())

    def _get_next_item(self) -> HospitalItem:
        sick_type = self._get_next_type()
        return HospitalItem(id=self.next_id, created_time=self.current_time, sick_type=sick_type)

    def _get_next_type(self) -> SickType:
        return random.choices(self.sick_types, self.sick_probas, k=1)[0]
