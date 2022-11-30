from qnet.base import Node, Metrics
from qnet.logger import MetricLoggerDispatcher, CLILogger

from .base import HospitalItem
from .factory import HospitalFactoryMetrics


class HospitalCLILogger(CLILogger[HospitalItem]):

    def _hospital_factory_metrics(self, metrics: HospitalFactoryMetrics) -> str:
        metrics_dict = self._factory_metrics(metrics)
        metrics_dict['mean_time_spent_in_hospital_by_sick_type'] = self._format_dict(metrics.mean_time_per_type,
                                                                                     join_chars='\n',
                                                                                     split_chars=': ',
                                                                                     start_chars='\n')
        return metrics_dict

    def _dispatch_metrics_logger(self, metrics: Metrics[Node[HospitalItem]]) -> MetricLoggerDispatcher:
        if isinstance(metrics, HospitalFactoryMetrics):
            return self._hospital_factory_metrics
        return super()._dispatch_metrics_logger(metrics)
