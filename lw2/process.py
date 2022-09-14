from typing import Any

from element import Element
from common import INF_TIME


class ProcessElement(Element):

    def __init__(self, max_queue_size: int, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.max_queue_size = max_queue_size
        self.queue_size = 0
        self.is_busy = False
        self.num_failures = 0
        self.next_time = INF_TIME

    def __str__(self) -> str:
        return self._get_state(['num_events', 'next_time', 'is_busy', 'queue_size', 'num_failures'])

    def start_action(self) -> None:
        if self.is_busy:
            if self.queue_size >= self.max_queue_size:
                self.num_failures += 1
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
