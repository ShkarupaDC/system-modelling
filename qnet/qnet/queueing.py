import itertools
from dataclasses import dataclass, field
from typing import Iterator, Iterable, Optional, Generic, ClassVar, TypeVar, Any

from .common import INF_TIME, TIME_EPS, I, T, SupportsDict, BoundedCollection, MinHeap
from .node import Node, NodeMetrics

QM = TypeVar('QM', bound='QueueingMetrics')


@dataclass(eq=False)
class QueueingMetrics(NodeMetrics):
    total_wait_time: float = field(init=False, default=0)
    load_time_per_channel: dict[int, float] = field(init=False, default_factory=dict)
    in_time: float = field(init=False, default=0)
    out_time: float = field(init=False, default=0)
    in_intervals_sum: float = field(init=False, default=0)
    out_intervals_sum: float = field(init=False, default=0)
    num_failures: int = field(init=False, default=0)

    @property
    def mean_in_interval(self) -> float:
        return self.in_intervals_sum / max(self.num_in - 1, 1)

    @property
    def mean_out_interval(self) -> float:
        return self.out_intervals_sum / max(self.num_out - 1, 1)

    @property
    def mean_queuelen(self) -> float:
        return self.total_wait_time / max(self.passed_time, TIME_EPS)

    @property
    def mean_load_per_channel(self) -> dict[int, float]:
        return {
            channel: load_time / max(self.passed_time, TIME_EPS)
            for channel, load_time in self.load_time_per_channel.items()
        }

    @property
    def mean_channels_load(self) -> float:
        return sum(self.mean_load_per_channel.values())

    @property
    def failure_proba(self) -> float:
        return self.num_failures / max(self.num_in, 1)

    @property
    def mean_wait_time(self) -> float:
        return self.total_wait_time / max(self.num_out, 1)

    @property
    def mean_load_time_per_channel(self) -> dict[int, float]:
        return {channel: load_time / max(self.num_out, 1) for channel, load_time in self.load_time_per_channel.items()}

    @property
    def mean_load_time(self) -> float:
        return sum(self.mean_load_time_per_channel.values())


@dataclass(order=True, unsafe_hash=True)
class Task(SupportsDict, Generic[T]):
    id_gen: ClassVar[Iterator[int]] = itertools.count()

    id: int = field(init=False, repr=False, compare=False)
    item: T = field(compare=False)
    next_time: float

    def __post_init__(self) -> None:
        self.id = next(self.id_gen)

    def to_dict(self) -> dict[str, Any]:
        return {'item': self.item, 'next_time': self.next_time}


@dataclass(eq=False)
class Channel(SupportsDict, Generic[T]):
    id: int

    def to_dict(self) -> dict[str, Any]:
        return {'id': self.id}


class ChannelPool(SupportsDict, Generic[T]):

    def __init__(self, max_channels: Optional[int] = None) -> None:
        self.max_channels = max_channels
        self.tasks = MinHeap[Task[T]](maxlen=max_channels)
        self.task_to_channel: dict[Task[T], Channel[T]] = {}
        self.current_id: int = 0
        self.free_channels = {Channel[T](self.current_id)}
        self.occupied_channels: set[Channel[T]] = set()

    @property
    def num_active_tasks(self) -> int:
        return len(self.tasks)

    @property
    def num_occupied_channels(self) -> int:
        return len(self.occupied_channels)

    @property
    def is_occupied(self) -> bool:
        return self.max_channels is not None and self.num_occupied_channels == self.max_channels

    @property
    def is_empty(self) -> bool:
        return self.num_occupied_channels == 0

    @property
    def next_finish_time(self) -> float:
        next_task = self.tasks.min
        return INF_TIME if next_task is None else next_task.next_time

    def clear(self) -> None:
        self.tasks.clear()
        self.task_to_channel.clear()
        self.current_id = 0
        self.free_channels = {Channel[T](self.current_id)}
        self.occupied_channels.clear()

    def add_task(self, task: Task[T]) -> None:
        channel = self._occupy_channel()
        self.tasks.push(task)
        self.task_to_channel[task] = channel

    def pop_finished_task(self) -> Task[T]:
        task = self.tasks.pop()
        self._free_channel(self.task_to_channel[task])
        return task

    def to_dict(self) -> dict[str, Any]:
        return {
            'max_channels': self.max_channels,
            'tasks': self.tasks,
            'current_id': self.current_id,
            'free_channels': self.free_channels,
            'occupied_channels': self.occupied_channels,
        }

    def _is_correct_id(self, channel_id: int) -> bool:
        return self.max_channels is None or channel_id < self.max_channels

    def _occupy_channel(self) -> Channel[T]:
        channel = self.free_channels.pop()
        if not self.free_channels and self._is_correct_id(self.current_id + 1):
            self.current_id += 1
            self.free_channels.add(Channel[T](self.current_id))
        self.occupied_channels.add(channel)
        return channel

    def _free_channel(self, channel: Channel[T]) -> None:
        self.free_channels.add(channel)
        self.occupied_channels.remove(channel)


class QueueingNode(Node[I, QM]):

    def __init__(self, queue: BoundedCollection[I], channel_pool: ChannelPool[I], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.queue = queue
        self.channel_pool = channel_pool
        self.next_time = INF_TIME

    @property
    def current_items(self) -> Iterable[I]:
        return itertools.chain(self.queue.data, (task.item for task in self.channel_pool.tasks.data))

    @property
    def num_tasks(self) -> int:
        return self.channel_pool.num_active_tasks

    @property
    def queuelen(self) -> int:
        return len(self.queue)

    def start_action(self, item: I) -> None:
        super().start_action(item)
        if self.channel_pool.is_occupied:
            if self.queue.is_full:
                self._failure_hook()
            else:
                self.queue.push(item)
        else:
            task = Task[I](item=item, next_time=self._predict_item_time(item=item))
            self.add_task(task)

    def end_action(self) -> I:
        item = self.channel_pool.pop_finished_task().item
        if not self.queue.is_empty:
            next_item = self.queue.pop()
            task = Task[I](item=next_item, next_time=self._predict_item_time(item=next_item))
            self.add_task(task)
        else:
            self.next_time = self._predict_next_time()
        return self._end_action(item)

    def reset(self) -> None:
        super().reset()
        self.next_time = INF_TIME
        self.queue.clear()
        self.channel_pool.clear()

    def add_task(self, task: Task[I]) -> None:
        self._before_add_task_hook(task)
        self.channel_pool.add_task(task)
        self.next_time = self._predict_next_time()

    def to_dict(self) -> dict[str, Any]:
        node_dict = super().to_dict()
        node_dict.update({
            'channel_pool': self.channel_pool,
            'queue': self.queue,
            'num_failures': self.metrics.num_failures
        })
        return node_dict

    def _predict_item_time(self, **kwargs: Any) -> float:
        return self.current_time + self._get_delay(**kwargs)

    def _predict_next_time(self, **_: Any) -> float:
        return self.channel_pool.next_finish_time

    def _before_time_update_hook(self, time: float) -> None:
        super()._before_time_update_hook(time)
        dtime = time - self.current_time
        for channel in self.channel_pool.occupied_channels:
            self.metrics.load_time_per_channel[channel.id] = self.metrics.load_time_per_channel.get(channel.id,
                                                                                                    0) + dtime
        self.metrics.total_wait_time += self.queuelen * dtime

    def _item_out_hook(self, item: I) -> None:
        super()._item_out_hook(item)
        if self.metrics.num_out > 1:
            self.metrics.out_intervals_sum += self.current_time - self.metrics.out_time
        self.metrics.out_time = self.current_time

    def _item_in_hook(self, item: I) -> None:
        super()._item_in_hook(item)
        if self.metrics.num_in > 1:
            self.metrics.in_intervals_sum += self.current_time - self.metrics.in_time
        self.metrics.in_time = self.current_time

    def _before_add_task_hook(self, _: Task[I]) -> None:
        pass

    def _failure_hook(self) -> None:
        self.metrics.num_failures += 1
