from typing import Any

from ..lib.base import Node, Metrics
from ..lib.logger import MetricLoggerDispatcher, Logger

from .base import HospitalItem
from .factory import HospitalFactoryMetrics


class HospitalLogger(Logger[HospitalItem]):

    def _time_dict(self, data: dict[Any, float]) -> str:
        return '\n'.join(f'{item}: {time:.{self.precision}f}' for item, time in data.items())

    def hospital_factory_metrics(self, metrics: HospitalFactoryMetrics) -> str:
        return (f'{self.node_metrics(metrics)}. '
                # f'Total time spent in hospital by person:\n{self._time_dict(metrics.time_per_item)}\n'
                f'Mean time spent in hospital by sick type:\n{self._time_dict(metrics.mean_time_per_type)}')

    def get_metrics_logger(self, metrics: Metrics[Node[HospitalItem]]) -> MetricLoggerDispatcher:
        if isinstance(metrics, HospitalFactoryMetrics):
            return self.hospital_factory_metrics
        return super().get_metrics_logger(metrics)