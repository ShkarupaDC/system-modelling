from typing import Any

from .common import T
from .base import Node, Item


class BaseFactoryNode(Node[T]):

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.next_time = self._predict_next_time()
        self.item: T = None

    def start_action(self, item: T) -> T:
        super().start_action(item)
        raise RuntimeError('This method must not be called!')


class FactoryNode(BaseFactoryNode[Item]):

    def end_action(self) -> Item:
        self.next_time = self._predict_next_time()
        self.item = Item(id=self.metrics.num_out, created=self.current_time)
        return self._end_action_hook(self.item)
