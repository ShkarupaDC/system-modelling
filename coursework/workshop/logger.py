from typing import Any

from qnet.base import Node, Metrics
from qnet.logger import MetricLoggerDispatcher, CLILogger

from .base import CarUnit
from .factory import CarUnitFactoryMetrics, Histogram


class WorkshopCLILogger(CLILogger[CarUnit]):

    def _format(self, value: Any) -> str:
        if isinstance(value, Histogram):
            histogram_dict = {
                self._format_bounds(value.bin_edges[idx], value.bin_edges[idx + 1]): count
                for idx, count in enumerate(value.values)
            }
            return self._format_dict(histogram_dict, join_chars='\n', split_chars=': ', start_chars='\n')
        return super()._format(value)

    def _format_bounds(self, start: float, end: float) -> str:
        return f'{self._format(start)} - {self._format(end)}'

    def _car_units_factory_metrics(self, metrics: CarUnitFactoryMetrics) -> str:
        metrics_dict = self._factory_metrics(metrics)
        metrics_dict.update({
            'mean_repair_time': metrics.mean_repair_time,
            'repair_time_std': metrics.repair_time_std,
            'repair_time_histogram': metrics.repair_time_histogram,
            'mean_num repairs': metrics.mean_num_repairs,
            'num_repairs_std': metrics.num_repairs_std,
            'num_repairs_histogram': metrics.num_repairs_histogram,
        })
        return metrics_dict

    def _dispatch_metrics_logger(self, metrics: Metrics[Node[CarUnit]]) -> MetricLoggerDispatcher:
        if isinstance(metrics, CarUnitFactoryMetrics):
            return self._car_units_factory_metrics
        return super()._dispatch_metrics_logger(metrics)
