import statistics
from dataclasses import dataclass
from typing import Type, Any

import numpy as np
import numpy.typing as npt

from qnet.base import ActionType
from qnet.factory import FactoryMetrics, BaseFactoryNode

from .base import CarUnit
from .queueing import RepairQueueingNode


@dataclass(eq=False)
class RepairInfo:
    time: float = 0
    num_repairs: int = 0


@dataclass(eq=False)
class CarUnitFactoryMetrics(FactoryMetrics[CarUnit]):

    @property
    def repair_info_per_unit(self) -> dict[CarUnit, RepairInfo]:
        repair_times: dict[CarUnit, float] = {}
        for item in self.items:
            if not item.processed:
                continue
            repair_info = RepairInfo()
            for idx, action in enumerate(item.history):
                if isinstance(action.node, RepairQueueingNode) and action.action_type == ActionType.OUT:
                    prev_action = item.history[idx - 1]
                    assert isinstance(
                        prev_action.node,
                        RepairQueueingNode) and prev_action.action_type == ActionType.IN, 'Invalid sequence of actions'
                    repair_info.num_repairs += 1
                    repair_info.time += action.time - prev_action.time
            repair_times[item] = repair_info
        return repair_times

    @property
    def mean_repair_time(self) -> float:
        return statistics.mean(info.time
                               for info in repair_infos.values()) if (repair_infos := self.repair_info_per_unit) else 0

    @property
    def repair_time_std(self) -> float:
        return statistics.stdev(info.time
                                for info in repair_infos.values()) if (repair_infos := self.repair_info_per_unit) else 0

    @property
    def repair_time_histogram(self) -> tuple[npt.NDArray, npt.NDArray]:
        return np.histogram(list(info.time for info in self.repair_info_per_unit.values()))

    @property
    def mean_num_repairs(self) -> float:
        return statistics.mean(info.num_repairs
                               for info in repair_infos.values()) if (repair_infos := self.repair_info_per_unit) else 0

    @property
    def num_repairs_std(self) -> float:
        return statistics.stdev(info.num_repairs
                                for info in repair_infos.values()) if (repair_infos := self.repair_info_per_unit) else 0

    @property
    def num_repairs_histogram(self) -> tuple[npt.NDArray, npt.NDArray]:
        return np.histogram(list(info.num_repairs for info in self.repair_info_per_unit.values()))


class CarUnitFactory(BaseFactoryNode[CarUnit]):

    def __init__(self, metrics_type: Type[CarUnitFactoryMetrics] = CarUnitFactoryMetrics, **kwargs: Any) -> None:
        self.metrics: CarUnitFactoryMetrics = None
        super().__init__(metrics_type=metrics_type, **kwargs)

    def _get_next_item(self) -> CarUnit:
        return CarUnit(id=self.next_id)
