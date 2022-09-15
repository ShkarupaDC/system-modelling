from dataclasses import dataclass
from typing import Any

from element import Element
from common import INF_TIME


@dataclass(eq=False, repr=False)
class ProcessStats:
    process: 'ProcessElement'
    wait_time: int = 0
    num_failures: int = 0

    def __str__(self) -> str:
        return f'Mean queue size: {self.mean_queue_size}. Mean wait time: {self.mean_wait_time}. Failure probability: {self.failure_proba}'

    @property
    def mean_queue_size(self) -> float:
        return self.wait_time / self.process.current_time

    @property
    def failure_proba(self) -> float:
        return self.num_failures / self.process.num_events

    @property
    def mean_wait_time(self) -> float:
        return self.wait_time / self.process.num_events


class ProcessElement(Element):

    def __init__(self, max_queue_size: int, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.max_queue_size = max_queue_size
        self.queue_size = 0
        self.is_busy = False
        self.stats = ProcessStats(self)

    def __str__(self) -> str:
        return self._get_str_state(['num_events', 'next_time', 'is_busy', 'queue_size', 'stats.num_failures'])

    def start_action(self) -> None:
        if self.is_busy:
            if self.queue_size >= self.max_queue_size:
                self.stats.num_failures += 1
            else:
                self.queue_size += 1
        else:
            self.is_busy = True
            self._update_next_time()

    def end_action(self) -> None:
        self.is_busy = False

        if self.queue_size > 0:
            self.queue_size -= 1
            self.is_busy = True
            self._update_next_time()
        else:
            self.next_time = INF_TIME

        super().end_action()

    def set_current_time(self, next_time: float) -> None:
        self.stats.wait_time += self.queue_size * (next_time - self.current_time)
        super().set_current_time(next_time)
