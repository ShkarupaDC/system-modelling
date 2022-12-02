import itertools
from dataclasses import dataclass, field
from typing import Iterable, Optional, Generic, TypeVar, Any

from .common import INF_TIME, TIME_EPS, I, T, BoundedCollection, MinHeap
from .node import Node, NodeMetrics

QM = TypeVar('QM', bound='QueueingMetrics')


@dataclass(eq=False)
class QueueingMetrics(NodeMetrics):
    wait_time: float = field(init=False, default=0)
    busy_time: float = field(init=False, default=0)
    in_time: float = field(init=False, default=0)
    out_time: float = field(init=False, default=0)
    in_interval: float = field(init=False, default=0)
    out_interval: float = field(init=False, default=0)
    num_failures: int = field(init=False, default=0)

    @property
    def mean_in_interval(self) -> float:
        return self.in_interval / max(self.num_in - 1, 1)

    @property
    def mean_out_interval(self) -> float:
        return self.out_interval / max(self.num_out - 1, 1)

    @property
    def mean_queuelen(self) -> float:
        return self.wait_time / max(self.passed_time, TIME_EPS)

    @property
    def mean_busy_channels(self) -> float:
        return self.busy_time / max(self.passed_time, TIME_EPS)

    @property
    def failure_proba(self) -> float:
        return self.num_failures / max(self.num_in, 1)

    @property
    def mean_wait_time(self) -> float:
        return self.wait_time / max(self.num_out, 1)

    @property
    def mean_busy_time(self) -> float:
        return self.busy_time / max(self.num_out, 1)


@dataclass(order=True)
class Channel(Generic[T]):
    item: T = field(compare=False)
    next_time: float


class QueueingNode(Node[I, QM]):

    def __init__(self, queue: BoundedCollection[I], max_channels: Optional[int] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.queue = queue
        self.channels = MinHeap[Channel[I]](maxlen=max_channels)
        self.next_time = INF_TIME

    @property
    def current_items(self) -> Iterable[I]:
        return itertools.chain(self.queue.data, (channel.item for channel in self.channels.data))

    @property
    def num_channels(self) -> int:
        return len(self.channels)

    @property
    def queuelen(self) -> int:
        return len(self.queue)

    def start_action(self, item: I) -> None:
        super().start_action(item)
        if self.channels.is_full:
            if self.queue.is_full:
                self._failure_hook()
            else:
                self.queue.push(item)
        else:
            channel = Channel[I](item=item, next_time=self._predict_item_time(item=item))
            self.add_channel(channel)

    def end_action(self) -> I:
        item = self.channels.pop().item
        if not self.queue.is_empty:
            next_item = self.queue.pop()
            channel = Channel[I](item=next_item, next_time=self._predict_item_time(item=next_item))
            self.add_channel(channel)
        else:
            self.next_time = self._predict_next_time()
        return self._end_action(item)

    def reset(self) -> None:
        super().reset()
        self.next_time = INF_TIME
        self.queue.clear()
        self.channels.clear()

    def add_channel(self, channel: Channel[I]) -> None:
        self._before_add_channel_hook(channel)
        self.channels.push(channel)
        self.next_time = self._predict_next_time()

    def _predict_item_time(self, **kwargs: Any) -> float:
        return self.current_time + self._get_delay(**kwargs)

    def _predict_next_time(self, **_: Any) -> float:
        next_channel = self.channels.min
        return INF_TIME if next_channel is None else next_channel.next_time

    def _before_time_update_hook(self, time: float) -> None:
        super()._before_time_update_hook(time)
        dtime = time - self.current_time
        self.metrics.wait_time += self.queuelen * dtime
        self.metrics.busy_time += self.num_channels * dtime

    def _item_out_hook(self, item: I) -> None:
        super()._item_out_hook(item)
        if self.metrics.num_out > 1:
            self.metrics.out_interval += self.current_time - self.metrics.out_time
        self.metrics.out_time = self.current_time

    def _item_in_hook(self, item: I) -> None:
        super()._item_in_hook(item)
        if self.metrics.num_in > 1:
            self.metrics.in_interval += self.current_time - self.metrics.in_time
        self.metrics.in_time = self.current_time

    def _before_add_channel_hook(self, _: Channel[I]) -> None:
        pass

    def _failure_hook(self) -> None:
        self.metrics.num_failures += 1
