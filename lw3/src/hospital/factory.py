import random
from dataclasses import dataclass
from typing import Type, Any

from ..lib.factory import BaseFactoryNode, FactoryMetrics

from .base import HospitalItem, SickType
from .utils import MeanMeter


@dataclass(eq=False)
class HospitalFactoryMetrics(FactoryMetrics[HospitalItem]):

    @property
    def mean_time_per_type(self) -> dict[SickType, float]:
        meters = {name: MeanMeter() for name in SickType}
        for sick, time in self.time_per_item.items():
            meters[sick.sick_type].update(time)
        return {name: meter.mean for name, meter in meters.items()}


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
