import statistics
from dataclasses import dataclass, field
from typing import Type, TypeVar, Any

from .common import T
from .base import Node, Metrics, Item

I = TypeVar('I', bound='Item')


@dataclass(eq=False)
class BaseFactoryMetrics(Metrics[Node[T]]):
    items: list[T] = field(init=False, default_factory=list)


class BaseFactoryNode(Node[T]):

    def __init__(self, metrics_type: Type[BaseFactoryMetrics[T]] = BaseFactoryMetrics, **kwargs: Any) -> None:
        self.metrics: BaseFactoryMetrics[T] = None
        super().__init__(metrics_type=metrics_type, **kwargs)
        self.item: T = None
        self.next_time = self._predict_next_time()

    def start_action(self, item: T) -> T:
        super().start_action(item)
        raise RuntimeError('This method must not be called!')


@dataclass(eq=False)
class FactoryMetrics(BaseFactoryMetrics[I]):

    @property
    def time_per_item(self) -> dict[I, float]:
        return {item: item.history[-1].time - item.history[0].time for item in self.items if item.processed}

    @property
    def mean_time(self) -> float:
        if time_data := self.time_per_item.values():
            return statistics.mean(time_data)
        return 0


class FactoryNode(BaseFactoryNode[Item]):

    def __init__(self, metrics_type: Type[FactoryMetrics[Item]] = FactoryMetrics, **kwargs: Any) -> None:
        self.metrics: FactoryMetrics[Item] = None
        super().__init__(metrics_type=metrics_type, **kwargs)

    def end_action(self) -> Item:
        self.next_time = self._predict_next_time()
        self.item = Item(id=self.metrics.num_out, created=self.current_time)
        self.metrics.items.append(self.item)
        return self._end_action_hook(self.item)
