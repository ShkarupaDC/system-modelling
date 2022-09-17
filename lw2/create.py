from typing import Any

from element import Element


class CreateElement(Element):

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.next_time = self._predict_next_time()

    def end_action(self) -> None:
        self.next_time = self._predict_next_time()
        super().end_action()
