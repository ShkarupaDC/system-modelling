from typing import Any

from qnet.common import I, PriorityQueue
from qnet.logger import CLILogger

from .model import Histogram


class WorkshopCLILogger(CLILogger[I]):

    # Formatters
    def _format(self, value: Any) -> str:
        if isinstance(value, PriorityQueue):
            return self._format_class(value, self._priority_queue(value))
        if isinstance(value, Histogram):
            return self._format_dict(self._histogram(value), join_chars='\n', split_chars=': ', start_chars='\n')
        return super()._format(value)

    def _format_bounds(self, start: float, end: float) -> str:
        return f'{self._format(start)} - {self._format(end)}'

    # Other
    def _histogram(self, histogram: Histogram) -> dict[str, Any]:
        return {
            self._format_bounds(histogram.bin_edges[idx], histogram.bin_edges[idx + 1]): value
            for idx, value in enumerate(histogram.values)
        }

    def _priority_queue(self, queue: PriorityQueue[I]) -> dict[str, Any]:
        metrics_dict = queue.to_dict()
        metrics_dict['items'] = queue.heap
        return metrics_dict
