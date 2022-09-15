from abc import ABC, abstractmethod
from typing import Callable, Optional

from common import format_param

GetDelayFn = Callable[[], float]


class Element(ABC):

    def __init__(self, name: str, get_delay: GetDelayFn, next_elements: Optional[list['Element']] = None) -> None:
        self.name = name
        self.get_delay = get_delay
        self.next_elements: list['Element'] = [] if next_elements is None else next_elements
        self.num_events = 0
        self.current_time = 0
        self.next_time = 0

    def __str__(self) -> str:
        return self._get_str_state(['num_events', 'next_time'])

    @abstractmethod
    def start_action(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def end_action(self) -> None:
        self.num_events += 1
        for element in self.next_elements:
            element.start_action()

    @abstractmethod
    def set_current_time(self, next_time: float) -> None:
        self.current_time = next_time

    def _update_next_time(self) -> None:
        self.next_time = self.current_time + self.get_delay()

    def _get_str_state(self, param_paths: list[str]) -> str:
        params = ', '.join([format_param(self, path) for path in param_paths])
        return f'{self.name} ({params})'
