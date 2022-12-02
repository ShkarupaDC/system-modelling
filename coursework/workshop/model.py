import statistics
from dataclasses import dataclass
from typing import SupportsFloat

import numpy as np
import numpy.typing as npt

from qnet.common import ActionType
from qnet.model import ModelMetrics

from .common import CarUnit
from .queueing import RepairQueueingNode

EPS = 1e-6


@dataclass(eq=False)
class RepairInfo:
    time: float = 0
    num_repairs: int = 0


@dataclass(eq=False)
class Histogram:
    values: npt.NDArray[np.float32]
    bin_edges: npt.NDArray[np.float32]


def _clip(x: SupportsFloat, xmin: SupportsFloat, xmax: SupportsFloat) -> SupportsFloat:
    return max(xmin, min(xmax, x))


@dataclass(eq=False)
class CarUnitModelMetrics(ModelMetrics[CarUnit]):

    @property
    def repair_info_per_unit(self) -> dict[CarUnit, RepairInfo]:
        repair_times: dict[CarUnit, RepairInfo] = {}
        for item in self.items:
            if not item.processed:
                continue
            repair_info = RepairInfo()
            for idx, in_action in enumerate(item.history):
                if isinstance(in_action.node, RepairQueueingNode) and in_action.action_type == ActionType.IN:
                    out_action = item.history[idx + 1]
                    assert isinstance(
                        out_action.node,
                        RepairQueueingNode) and out_action.action_type == ActionType.OUT, 'Invalid sequence of actions'
                    repair_info.num_repairs += 1
                    repair_info.time += out_action.time - in_action.time
            repair_times[item] = repair_info
        return repair_times

    @property
    def mean_repair_time(self) -> float:
        return statistics.mean(info.time
                               for info in repair_infos.values()) if (repair_infos := self.repair_info_per_unit) else 0

    @property
    def repair_time_std(self) -> float:
        return statistics.stdev(
            info.time for info in repair_infos.values()) if len(repair_infos := self.repair_info_per_unit) >= 2 else 0

    @property
    def repair_time_histogram(self) -> Histogram:
        repair_time = np.asarray(list(info.time for info in self.repair_info_per_unit.values()), dtype=float)
        return Histogram(*np.histogram(repair_time, bins=_clip(int(repair_time.size * 0.2), xmin=1, xmax=10)))

    @property
    def mean_num_repairs(self) -> float:
        return statistics.mean(info.num_repairs
                               for info in repair_infos.values()) if (repair_infos := self.repair_info_per_unit) else 0

    @property
    def num_repairs_std(self) -> float:
        return statistics.stdev(
            info.num_repairs
            for info in repair_infos.values()) if len(repair_infos := self.repair_info_per_unit) >= 2 else 0

    @property
    def num_repairs_histogram(self) -> Histogram:
        num_repairs = np.asarray(list(info.num_repairs for info in self.repair_info_per_unit.values()), dtype=int)
        return Histogram(*np.histogram(num_repairs, bins=0.5 + np.arange(0, num_repairs.max(initial=1.0) + EPS, 1.0)))
