import statistics
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Type, TypeVar, Any

from lib.common import T
from lib.base import Node, NodeMetrics, Item

I = TypeVar('I', bound='Item')


@dataclass(eq=False)
class BaseFactoryMetrics(NodeMetrics[Node[T]]):
    items: list[T] = field(init=False, default_factory=list)


class BaseFactoryNode(Node[T]):

    def __init__(self, metrics_type: Type[BaseFactoryMetrics[T]] = BaseFactoryMetrics, **kwargs: Any) -> None:
        self.metrics: BaseFactoryMetrics[T] = None
        super().__init__(metrics_type=metrics_type, **kwargs)
        self.item: T = None
        self.next_time = self._predict_next_time()

    @property
    def next_id(self) -> int:
        return self.metrics.num_out

    def start_action(self, item: T) -> T:
        super().start_action(item)
        raise RuntimeError('This method must not be called!')

    def end_action(self) -> T:
        self.item = self._get_next_item()
        self.metrics.items.append(self.item)
        self.next_time = self._predict_next_time()
        return self._end_action(self.item)

    def reset(self) -> None:
        super().reset()
        self.item = None
        self.next_time = self._predict_next_time()

    @abstractmethod
    def _get_next_item(self) -> T:
        raise NotImplementedError


@dataclass(eq=False)
class FactoryMetrics(BaseFactoryMetrics[I]):

    @property
    def time_per_item(self) -> dict[I, float]:
        return {item: item.released_time - item.created_time for item in self.items if item.processed}

    @property
    def mean_time(self) -> float:
        if time_data := self.time_per_item.values():
            return statistics.mean(time_data)
        return 0


class FactoryNode(BaseFactoryNode[Item]):

    def __init__(self, metrics_type: Type[FactoryMetrics[Item]] = FactoryMetrics, **kwargs: Any) -> None:
        self.metrics: FactoryMetrics[Item] = None
        super().__init__(metrics_type=metrics_type, **kwargs)

    def _get_next_item(self) -> Item:
        return Item(id=self.next_id)
