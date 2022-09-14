from abc import ABC, abstractmethod
from typing import Callable, Any, Optional

DelayFn = Callable[..., float]


class Element(ABC):

    def __init__(self,
                 name: str,
                 delay_fn: DelayFn,
                 delay_kwargs: dict[str, Any],
                 next_elements: Optional[list['Element']] = None) -> None:
        self.name = name
        self.delay_fn = delay_fn
        self.delay_kwargs = delay_kwargs
        self.next_elements: list['Element'] = [] if next_elements is None else next_elements
        self.num_events = 0
        self.current_time = 0
        self.next_time = 0

    def __str__(self) -> str:
        return self._get_state(['num_events', 'next_time'])

    def _get_state(self, param_names: list[str]) -> str:
        return f'{self.name} ({", ".join([f"{name}={getattr(self, name)}" for name in param_names])})'

    def _get_delay(self) -> float:
        return self.delay_fn(**self.delay_kwargs)

    def _update_next_time(self) -> None:
        self.next_time = self.current_time + self._get_delay()

    @abstractmethod
    def start_action(self) -> None:
        pass

    @abstractmethod
    def end_action(self) -> None:
        self.num_events += 1
        for element in self.next_elements:
            element.start_action()
