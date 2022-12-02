from dataclasses import dataclass

from qnet.model import ModelMetrics

from .common import HospitalItem, SickType
from .utils import MeanMeter


@dataclass(eq=False)
class HospitalModelMetrics(ModelMetrics[HospitalItem]):

    @property
    def mean_time_per_type(self) -> dict[SickType, float]:
        meters = {name: MeanMeter() for name in SickType}
        for sick, time in self.time_per_item.items():
            meters[sick.sick_type].update(time)
        return {name: meter.mean for name, meter in meters.items()}
