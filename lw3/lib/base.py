from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Generic, Iterable, Optional, Type, Any

from .common import T

DelayFn = Callable[..., float]


@dataclass(eq=False)
class Item:
    id: int


@dataclass(eq=False)
class Stats(Generic[T]):
    node: T
    num_in: int = field(init=False, default=0)
    num_out: int = field(init=False, default=0)


class Node(ABC, Generic[T]):

    def __init__(self,
                 get_delay: DelayFn,
                 next_node: Optional['Node[T]'] = None,
                 stats_type: Type[Stats['Node[T]']] = Stats) -> None:
        self.get_delay = get_delay
        self.next_node = next_node
        self.stats = stats_type(self)
        self.prev_node: Optional[Node[T]] = None
        self.current_time: float = 0
        self.next_time: float = 0

    @property
    def connected_nodes(self) -> Iterable['Node[T]']:
        return [self.next_node]

    def start_action(self, _: T) -> None:
        self.stats.num_in += 1

    @abstractmethod
    def end_action(self) -> T:
        raise NotImplementedError

    def update_time(self, time: float) -> None:
        self.current_time = time

    def set_next_node(self, node: 'Node[T]') -> None:
        self.next_node = node
        if node is not None:
            node.prev_node = self

    def _predict_next_time(self, **kwargs: Any) -> float:
        return self.current_time + self.get_delay(**kwargs)

    def _end_action_hook(self, item: T) -> T:
        self.stats.num_out += 1
        self._start_next_action(item)
        return item

    def _start_next_action(self, item: T) -> None:
        if self.next_node is not None:
            self.next_node.start_action(item)
