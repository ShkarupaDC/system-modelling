from typing import Any

from qnet.common import I, PriorityQueue
from qnet.logger import MetricsLoggerDispatcher, CLILogger
from qnet.model import ModelMetrics

from .model import CarUnitModelMetrics, Histogram


class WorkshopCLILogger(CLILogger[I]):

    # Formatters
    def _format(self, value: Any) -> str:
        class_name = value.__class__.__name__
        if isinstance(value, Histogram):
            histogram_dict = {
                self._format_bounds(value.bin_edges[idx], value.bin_edges[idx + 1]): count
                for idx, count in enumerate(value.values)
            }
            return self._format_dict(histogram_dict, join_chars='\n', split_chars=': ', start_chars='\n')
        if isinstance(value, PriorityQueue):
            return f'{class_name}({self._format(self._priority_queue(value))})'
        return super()._format(value)

    def _format_bounds(self, start: float, end: float) -> str:
        return f'{self._format(start)} - {self._format(end)}'

    # Other
    def _priority_queue(self, queue: PriorityQueue[I]) -> dict[str, Any]:
        metrics_dict = self._bounded_collection(queue)
        metrics_dict['items'] = queue.heap
        return metrics_dict

    # Model Metrics
    def _car_unit_model_metrics(self, metrics: CarUnitModelMetrics) -> str:
        metrics_dict = self._model_metrics(metrics)
        metrics_dict.update({
            'mean_repair_time': metrics.mean_repair_time,
            'repair_time_std': metrics.repair_time_std,
            'repair_time_histogram': metrics.repair_time_histogram,
            'mean_num repairs': metrics.mean_num_repairs,
            'num_repairs_std': metrics.num_repairs_std,
            'num_repairs_histogram': metrics.num_repairs_histogram,
        })
        return metrics_dict

    def _dispatch_model_metrics_logger(self, metrics: ModelMetrics) -> MetricsLoggerDispatcher:
        if isinstance(metrics, CarUnitModelMetrics):
            return self._car_unit_model_metrics
        return super()._dispatch_model_metrics_logger(metrics)
