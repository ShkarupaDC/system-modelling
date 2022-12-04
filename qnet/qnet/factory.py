import itertools
from abc import abstractmethod
from typing import Iterable, Optional, Any

from .common import I, Item
from .node import NM, Node
from .utils import filter_none


class BaseFactoryNode(Node[I, NM]):

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.item: Optional[I] = None
        self.next_time = self._predict_next_time()
        self.counter = itertools.count()

    @property
    def current_items(self) -> Iterable[I]:
        return filter_none((self.item, ))

    @property
    def next_id(self) -> str:
        return f'{self.num_nodes}_{next(self.counter)}'

    def start_action(self, item: I) -> None:
        super().start_action(item)
        raise RuntimeError('This method must not be called!')

    def end_action(self) -> I:
        self.item = self._get_next_item()
        self.next_time = self._predict_next_time()
        return self._end_action(self.item)

    def reset(self) -> None:
        super().reset()
        self.item = None
        self.next_time = self._predict_next_time()

    def to_dict(self) -> dict[str, Any]:
        node_dict = super().to_dict()
        node_dict.update({'last_item': self.item, 'last_created_time': self.item.created_time if self.item else None})
        return node_dict

    @abstractmethod
    def _get_next_item(self) -> I:
        raise NotImplementedError


class FactoryNode(BaseFactoryNode[Item, NM]):

    def _get_next_item(self) -> Item:
        return Item(id=self.next_id, created_time=self.current_time)
