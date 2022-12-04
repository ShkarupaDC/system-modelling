from abc import ABC, abstractmethod
import inspect
from dataclasses import dataclass, field
from typing import Callable, Generic, Iterable, Optional, TypeVar, Any, cast

from .common import I, SupportsDict, Metrics, ActionRecord, ActionType
from .utils import filter_none

NM = TypeVar('NM', bound='NodeMetrics')

DelayFn = Callable[..., float]


@dataclass(eq=False)
class NodeMetrics(Metrics):
    node_name: str = field(init=False, default='')
    num_in: int = field(init=False, default=0)
    num_out: int = field(init=False, default=0)
    start_action_time: float = field(init=False, default=-1)
    end_action_time: float = field(init=False, default=-1)

    def to_dict(self) -> dict[str, Any]:
        metrics_dict = super().to_dict()
        metrics_dict.update({'num_in': self.num_in, 'num_out': self.num_out})
        return metrics_dict


class Node(ABC, SupportsDict, Generic[I, NM]):
    num_nodes: int = 0

    def __init__(self,
                 delay_fn: DelayFn,
                 metrics: NM,
                 name: Optional[str] = None,
                 next_node: Optional['Node[I, NodeMetrics]'] = None) -> None:
        self.num_nodes += 1
        self.delay_fn = delay_fn
        self.delay_params = inspect.signature(self.delay_fn).parameters
        self.metrics = metrics
        self.name = self._get_auto_name() if name is None else name
        self.metrics.node_name = self.name
        self.next_node = next_node
        self.prev_node: Optional[Node[I, NodeMetrics]] = None
        self.current_time: float = 0
        self.next_time: float = 0

    @property
    def connected_nodes(self) -> Iterable['Node[I, NodeMetrics]']:
        return filter_none((self.prev_node, self.next_node))

    @property
    def current_items(self) -> Iterable[I]:
        return []

    def start_action(self, item: I) -> None:
        self._item_in_hook(item)
        self.metrics.start_action_time = self.current_time
        item.history.append(ActionRecord(self, ActionType.IN, self.current_time))

    @abstractmethod
    def end_action(self) -> I:
        raise NotImplementedError

    def update_time(self, time: float) -> None:
        self._before_time_update_hook(time)
        self.current_time = time
        for item in self.current_items:
            item.current_time = self.current_time

    def set_next_node(self, node: Optional['Node[I, NodeMetrics]']) -> None:
        self.next_node = node
        if node is not None:
            node.prev_node = cast(Node[I, NodeMetrics], self)

    def reset_metrics(self) -> None:
        self.metrics.reset()

    def reset(self) -> None:
        self.current_time = 0
        self.next_time = 0
        self.reset_metrics()

    def to_dict(self) -> dict[str, Any]:
        return {'next_time': self.next_time}

    def _get_auto_name(self) -> str:
        return f'{self.__class__.__name__}{self.num_nodes}'

    def _get_delay(self, **kwargs: Any) -> float:
        return self.delay_fn(**{name: value for name, value in kwargs.items() if name in self.delay_params})

    def _predict_next_time(self, **kwargs: Any) -> float:
        return self.current_time + self._get_delay(**kwargs)

    def _end_action(self, item: I) -> I:
        self._item_out_hook(item)
        self.metrics.end_action_time = self.current_time
        item.history.append(ActionRecord(self, ActionType.OUT, self.current_time))
        self._start_next_action(item)
        return item

    def _start_next_action(self, item: I) -> None:
        if self.next_node is None:
            item.processed = True
        else:
            self.next_node.start_action(item)

    def _item_in_hook(self, _: I) -> None:
        self.metrics.num_in += 1

    def _item_out_hook(self, _: I) -> None:
        self.metrics.num_out += 1

    def _before_time_update_hook(self, time: float) -> None:
        self.metrics.passed_time += time - self.current_time
