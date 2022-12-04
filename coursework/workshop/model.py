import statistics
from dataclasses import dataclass
from typing import Iterable, Any

import numpy as np
import numpy.typing as npt

from qnet.model import ModelMetrics

from .common import CarUnit

EPS = 1e-6


@dataclass(eq=False)
class Histogram:
    values: npt.NDArray[np.float32]
    bin_edges: npt.NDArray[np.float32]


@dataclass(eq=False)
class CarUnitModelMetrics(ModelMetrics[CarUnit]):

    @property
    def repair_wait_times(self) -> Iterable[CarUnit]:
        return (item.repair_wait_time for item in self.processed_items)

    @property
    def repair_wait_time_mean(self) -> float:
        try:
            return statistics.mean(self.repair_wait_times)
        except statistics.StatisticsError:
            return 0

    @property
    def repair_wait_time_std(self) -> float:
        try:
            return statistics.stdev(self.repair_wait_times)
        except statistics.StatisticsError:
            return 0

    @property
    def repair_wait_time_histogram(self) -> Histogram:
        times = np.asarray(list(self.repair_wait_times))
        if times.size > 0:
            num_bins = 15
            bins = np.empty(num_bins)
            bins[-1] = times.max()
            bins[:-1] = np.linspace(0, times.mean() + times.std(), num_bins - 1)
        else:
            bins = 1
        return Histogram(*np.histogram(times, bins=bins))

    @property
    def num_repairs(self) -> Iterable[CarUnit]:
        return (item.num_repairs for item in self.processed_items)

    @property
    def num_repairs_mean(self) -> float:
        try:
            return statistics.mean(self.num_repairs)
        except statistics.StatisticsError:
            return 0

    @property
    def num_repairs_std(self) -> float:
        try:
            return statistics.stdev(self.num_repairs)
        except statistics.StatisticsError:
            return 0

    @property
    def num_repairs_histogram(self) -> Histogram:
        num_repairs = np.asarray(list(self.num_repairs))
        bins = 0.5 + np.arange(num_repairs.max(initial=1.0) + EPS)
        return Histogram(*np.histogram(num_repairs, bins=bins))

    def to_dict(self) -> dict[str, Any]:
        metrics_dict = super().to_dict()
        for metric_name in ('repair_wait_times', 'num_repairs'):
            metrics_dict.pop(metric_name)
        return metrics_dict
