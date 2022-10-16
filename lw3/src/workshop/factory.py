import statistics
from dataclasses import dataclass
from typing import Type, Any

import numpy as np
import numpy.typing as npt

from lib.base import ActionType
from lib.factory import FactoryMetrics, BaseFactoryNode

from .base import CarUnit
from .queueing import RepairQueueingNode


@dataclass(eq=False)
class CarUnitFactoryMetrics(FactoryMetrics[CarUnit]):

    @property
    def repair_time_per_unit(self) -> dict[CarUnit, float]:
        repair_times: dict[CarUnit, float] = {}
        for item in self.items:
            if not item.processed:
                continue
            repair_time = 0
            for idx, action in enumerate(item.history):
                if isinstance(action.node, RepairQueueingNode) and action.action_type == ActionType.OUT:
                    prev_action = item.history[idx - 1]
                    assert isinstance(
                        prev_action.node,
                        RepairQueueingNode) and prev_action.action_type == ActionType.IN, 'Invalid sequence of actions'
                    repair_time += action.time - prev_action.time
            repair_times[item] = repair_time
        return repair_times

    @property
    def mean_repair_time(self) -> float:
        if repair_times := self.repair_time_per_unit:
            return statistics.mean(repair_times.values())
        return 0

    @property
    def repair_time_std(self) -> float:
        if repair_times := self.repair_time_per_unit:
            return statistics.stdev(repair_times.values())
        return 0

    @property
    def repair_time_histogram(self) -> tuple[npt.NDArray, npt.NDArray]:
        return np.histogram(list(self.repair_time_per_unit.values()))


class CarUnitFactory(BaseFactoryNode[CarUnit]):

    def __init__(self, metrics_type: Type[CarUnitFactoryMetrics] = CarUnitFactoryMetrics, **kwargs: Any) -> None:
        self.metrics: CarUnitFactoryMetrics = None
        super().__init__(metrics_type=metrics_type, **kwargs)

    def _get_next_item(self) -> CarUnit:
        return CarUnit(id=self.next_id)
