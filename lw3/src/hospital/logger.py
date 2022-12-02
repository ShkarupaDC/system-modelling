from typing import Any

from qnet.logger import MetricsLoggerDispatcher, CLILogger
from qnet.model import ModelMetrics

from .common import HospitalItem
from .model import HospitalModelMetrics


class HospitalCLILogger(CLILogger[HospitalItem]):

    def _hospital_model_metrics(self, metrics: HospitalModelMetrics) -> dict[str, Any]:
        metrics_dict = self._model_metrics(metrics)
        metrics_dict['mean_time_spent_in_hospital_by_sick_type'] = self._format_dict(metrics.mean_time_per_type,
                                                                                     join_chars='\n',
                                                                                     split_chars=': ',
                                                                                     start_chars='\n')
        return metrics_dict

    def _dispatch_model_metrics_logger(self, metrics: ModelMetrics[HospitalItem]) -> MetricsLoggerDispatcher:
        if isinstance(metrics, HospitalModelMetrics):
            return self._hospital_model_metrics
        return super()._dispatch_model_metrics_logger(metrics)
