from abc import ABC, abstractmethod
from enum import Enum
import inspect
from dataclasses import dataclass, field
from typing import Callable, Generic, Iterable, Optional, Type, Any

from .common import T

DelayFn = Callable[..., float]


class ActionType(str, Enum):
    IN = 'in'
    OUT = 'out'


@dataclass(eq=False)
class ActionRecord:
    node_name: str
    action_type: ActionType
    time: float


@dataclass(eq=False)
class Item:
    id: int = 0
    history: list[ActionRecord] = field(repr=False, default_factory=list)


@dataclass(eq=False)
class Metrics(Generic[T]):
    node: T
    num_in: int = field(init=False, default=0)
    num_out: int = field(init=False, default=0)


class Node(ABC, Generic[T]):
    num_nodes: int = 0

    def __init__(self,
                 delay_fn: DelayFn,
                 name: Optional[str] = None,
                 next_node: Optional['Node[T]'] = None,
                 metrics_type: Type[Metrics['Node[T]']] = Metrics) -> None:
        self.num_nodes += 1
        self.delay_fn = delay_fn
        self.name = self._get_auto_name() if name is None else name
        self.next_node = next_node
        self.metrics = metrics_type(self)
        self.prev_node: Optional[Node[T]] = None
        self.current_time: float = 0
        self.next_time: float = 0

    @property
    def connected_nodes(self) -> Iterable['Node[T]']:
        return [self.next_node]

    def start_action(self, item: T) -> None:
        if isinstance(item, Item):
            item.history.append(ActionRecord(self.name, ActionType.IN, self.current_time))
        self.metrics.num_in += 1

    @abstractmethod
    def end_action(self) -> T:
        raise NotImplementedError

    def update_time(self, time: float) -> None:
        self.current_time = time

    def set_next_node(self, node: 'Node[T]') -> None:
        self.next_node = node
        if node is not None:
            node.prev_node = self

    def _get_auto_name(self) -> str:
        return f'{self.__class__.__name__}{self.num_nodes}'

    def _predict_next_time(self, **kwargs: Any) -> float:
        if inspect.signature(self.delay_fn).parameters:
            delay = self.delay_fn(**kwargs)
        else:
            delay = self.delay_fn()
        return self.current_time + delay

    def _end_action_hook(self, item: T) -> T:
        if isinstance(item, Item):
            item.history.append(ActionRecord(self.name, ActionType.OUT, self.current_time))
        self.metrics.num_out += 1
        self._start_next_action(item)
        return item

    def _start_next_action(self, item: T) -> None:
        if self.next_node is not None:
            self.next_node.start_action(item)
