import random
from dataclasses import dataclass, field
from typing import Any, Type

from ..lib.base import Metrics
from ..lib.factory import BaseFactoryNode

from .base import HospitalItem, SickType


@dataclass(eq=False)
class HospitalFactoryMetrics(Metrics[HospitalItem]):
    items: list[HospitalItem] = field(init=False, default_factory=list)

    @property
    def total_time(self) -> dict[HospitalItem, float]:
        return {item: item.history[-1].time - item.history[0].time for item in self.items if item.processed}


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
        self.item = HospitalItem(id=self.metrics.num_out, created=self.current_time, sick_type=sick_type)
        self.metrics.items.append(self.item)
        self.next_time = self._predict_next_time()
        return self._end_action_hook(self.item)

    def _get_next_type(self) -> SickType:
        return random.choices(self.sick_types, self.sick_probas, k=1)[0]
