import random
from dataclasses import dataclass, field
from typing import Any, Type

from ..lib.base import Metrics
from ..lib.factory import BaseFactoryNode

from .base import HospitalItem, SickType


@dataclass(eq=False)
class HospitalFactoryMetrics(Metrics[HospitalItem]):
    items: list[HospitalItem] = field(init=False, default_factory=list)


class HospitalFactoryNode(BaseFactoryNode[HospitalItem]):

    def __init__(self,
                 probas: dict[SickType, float],
                 metrics_type: Type[HospitalFactoryMetrics] = HospitalFactoryMetrics,
                 **kwargs: Any) -> None:
        self.metrics: HospitalFactoryMetrics = None
        super().__init__(metrics_type=metrics_type, **kwargs)
        self.sick_types, self.sick_probas = zip(*probas.items())

    def end_action(self) -> HospitalItem:
        sick_type = self._get_next_type()
        item = HospitalItem(id=self.metrics.num_out, sick_type=sick_type)
        self.metrics.items.append(item)
        return self._end_action_hook(item)

    def _get_next_type(self) -> SickType:
        return random.choices(self.sick_types, self.sick_probas, k=1)[0]
