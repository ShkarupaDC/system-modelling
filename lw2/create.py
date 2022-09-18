from dataclasses import dataclass
from typing import Any

from element import Element, Stats


@dataclass(eq=False)
class CreateStats(Stats):

    def __repr__(self) -> str:
        return f'Num created: {self.num_events}.'


class CreateElement(Element):

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.next_time = self._predict_next_time()
        self.stats = CreateStats(self)

    def end_action(self) -> None:
        self.next_time = self._predict_next_time()
        super().end_action()
