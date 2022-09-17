import random
from dataclasses import dataclass, field
from typing import Callable, Optional

from common import format_params, instance_counter

GetDelayFn = Callable[[], float]


@dataclass(eq=False)
class Stats:
    element: 'Element'
    num_events: int = field(init=False, default=0)

    def __repr__(self) -> str:
        return f'Num events: {self.num_events}'


@instance_counter
class Element:

    def __init__(self, get_delay: GetDelayFn, name: Optional[str] = None) -> None:
        self.name = self._get_name() if name is None else name
        self.get_delay = get_delay
        self.current_time = 0
        self.next_time = 0
        self.next_elements: list[Element] = []
        self.next_probas: list[float] = []
        self.stats = Stats(self)

    def _get_name(self) -> str:
        return f'{self.__class__.__name__}{self._next_id()}'  # pylint: disable=no-member

    def _get_str_state(self) -> str:
        return format_params(self, ['stats.num_events', ('next_time', '{value:.5f}')])

    def __repr__(self) -> str:
        return f'{self.name} ({self._get_str_state()})'

    def start_action(self) -> None:
        pass

    def end_action(self) -> None:
        self.stats.num_events += 1
        if self.next_elements:
            self._get_next_element().start_action()

    def set_current_time(self, next_time: float) -> None:
        self.current_time = next_time

    def add_next_element(self, element: 'Element', proba: float = 1.0) -> None:
        self.next_probas.append(proba)
        self.next_elements.append(element)

    def _get_next_element(self) -> 'Element':
        return random.choices(self.next_elements, weights=self.next_probas, k=1)[0]

    def _predict_next_time(self) -> float:
        return self.current_time + self.get_delay()
