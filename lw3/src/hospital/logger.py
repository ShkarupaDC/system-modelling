from ..lib.base import Node, Metrics
from ..lib.logger import MetricLoggerDispatcher, Logger

from .base import HospitalItem
from .factory import HospitalFactoryMetrics


class HospitalLogger(Logger[HospitalItem]):

    def hospital_factory_metrics(self, metrics: HospitalFactoryMetrics) -> str:
        return (f'{self.node_metrics(metrics)}. '
                f'Total time spent in hospital by person:\n' +
                '\n'.join(f'{person}: {time:.{self.precision}f}' for person, time in metrics.total_time.items()))

    def get_metrics_logger(self, metrics: Metrics[Node[HospitalItem]]) -> MetricLoggerDispatcher:
        if isinstance(metrics, HospitalFactoryMetrics):
            return self.hospital_factory_metrics
        return super().get_metrics_logger(metrics)
