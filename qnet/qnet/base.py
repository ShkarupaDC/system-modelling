from abc import ABC, abstractmethod
from enum import Enum
import inspect
from dataclasses import dataclass, field, fields, _MISSING_TYPE
from typing import Callable, Generic, Iterable, Optional, Type, Any

from qnet.common import T

DelayFn = Callable[..., float]


class ActionType(str, Enum):
    IN = 'in'
    OUT = 'out'


@dataclass(eq=False)
class ActionRecord:
    node: 'Node[Item]'
    action_type: ActionType
    time: float


@dataclass(eq=False)
class Item:
    id: int = 0
    processed: bool = field(init=False, repr=False, default=False)
    history: list[ActionRecord] = field(init=False, repr=False, default_factory=list)

    @property
    def created_time(self) -> float:
        return self.history[0].time

    @property
    def last_time(self) -> float:
        return self.history[-1].time

    @property
    def released_time(self) -> Optional[float]:
        return self.last_time if self.processed else 0

    @property
    def time_in_system(self) -> float:
        return self.last_time - self.created_time


@dataclass(eq=False)
class Metrics(Generic[T]):
    parent: T

    def reset(self) -> None:
        for param in fields(self):
            if not isinstance(param.default, _MISSING_TYPE):
                default = param.default
            elif not isinstance(param.default_factory, _MISSING_TYPE):
                default = param.default_factory()
            else:
                continue
            setattr(self, param.name, default)


@dataclass(eq=False)
class NodeMetrics(Metrics[T]):
    num_in: int = field(init=False, default=0)
    num_out: int = field(init=False, default=0)


class Node(ABC, Generic[T]):
    num_nodes: int = 0

    def __init__(self,
                 delay_fn: DelayFn,
                 name: Optional[str] = None,
                 next_node: Optional['Node[T]'] = None,
                 metrics_type: Type[NodeMetrics['Node[T]']] = NodeMetrics) -> None:
        self.num_nodes += 1
        self.delay_fn = delay_fn
        self.delay_params = inspect.signature(self.delay_fn).parameters
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
        self._item_in_hook(item)
        if isinstance(item, Item):
            item.history.append(ActionRecord(self, ActionType.IN, self.current_time))

    @abstractmethod
    def end_action(self) -> T:
        raise NotImplementedError

    def update_time(self, time: float) -> None:
        self._before_time_update_hook(time)
        self.current_time = time

    def set_next_node(self, node: 'Node[T]') -> None:
        self.next_node = node
        if node is not None:
            node.prev_node = self

    def reset(self) -> None:
        self.current_time = 0
        self.next_time = 0
        self.metrics.reset()

    def _get_auto_name(self) -> str:
        return f'{self.__class__.__name__}{self.num_nodes}'

    def _get_delay(self, **kwargs: Any) -> float:
        return self.delay_fn(**{name: value for name, value in kwargs.items() if name in self.delay_params})

    def _predict_next_time(self, **kwargs: Any) -> float:
        return self.current_time + self._get_delay(**kwargs)

    def _end_action(self, item: T) -> T:
        self._item_out_hook(item)
        if isinstance(item, Item):
            item.history.append(ActionRecord(self, ActionType.OUT, self.current_time))
        self._start_next_action(item)
        return item

    def _start_next_action(self, item: T) -> None:
        if self.next_node is not None:
            self.next_node.start_action(item)
        else:
            if isinstance(item, Item):
                item.processed = True

    def _item_in_hook(self, _: T) -> None:
        self.metrics.num_in += 1

    def _item_out_hook(self, _: T) -> None:
        self.metrics.num_out += 1

    def _before_time_update_hook(self, _: float) -> None:
        pass
