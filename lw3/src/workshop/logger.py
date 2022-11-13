import numpy.typing as npt

from qnet.base import Node, Metrics
from qnet.logger import MetricLoggerDispatcher, Logger

from .base import CarUnit
from .factory import CarUnitFactoryMetrics


class WorkshopLogger(Logger[CarUnit]):

    def histogram(self, values: npt.NDArray, bin_edges: npt.NDArray) -> str:
        return '\n'.join(
            f'{idx}. {self.float(bin_edges[idx])} - {self.float(bin_edges[idx + 1])}: {self.float(value) if isinstance(value, float) else value}'
            for idx, value in enumerate(values))

    def car_units_factory_metrics(self, metrics: CarUnitFactoryMetrics) -> str:
        return (f'{self.factory_metrics(metrics)}. '
                f'Mean repair time: {self.float(metrics.mean_repair_time)}. '
                f'Repair time std: {self.float(metrics.repair_time_std)}. '
                f'Repair time histogram:\n{self.histogram(*metrics.repair_time_histogram)}\n'
                f'Mean num repairs: {self.float(metrics.mean_num_repairs)}. '
                f'Num repairs std: {self.float(metrics.num_repairs_std)}. '
                f'Num repairs histogram:\n{self.histogram(*metrics.num_repairs_histogram)}\n')

    def get_metrics_logger(self, metrics: Metrics[Node[CarUnit]]) -> MetricLoggerDispatcher:
        if isinstance(metrics, CarUnitFactoryMetrics):
            return self.car_units_factory_metrics
        return super().get_metrics_logger(metrics)
