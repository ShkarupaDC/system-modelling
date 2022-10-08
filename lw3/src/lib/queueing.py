from collections import deque
import heapq
from dataclasses import dataclass, field
from typing import Optional, Generic, Type, TypeVar, Any

from .common import INF_TIME, TIME_EPS, T
from .base import Node, Metrics

Q = TypeVar('Q', bound='QueueingNode')


class Queue(Generic[T]):

    def __init__(self, maxlen: Optional[int] = None) -> None:
        self.queue: deque[T] = deque(maxlen=maxlen)

    def __len__(self) -> int:
        return len(self.queue)

    @property
    def bounded(self) -> bool:
        return self.maxlen is not None

    @property
    def maxlen(self) -> Optional[int]:
        return self.queue.maxlen

    @property
    def is_empty(self) -> bool:
        return len(self) == 0

    @property
    def is_full(self) -> bool:
        return self.bounded and len(self) == self.maxlen

    def push(self, item: T) -> None:
        self.queue.append(item)

    def pop(self) -> T:
        return self.queue.popleft()


class MinHeap(Generic[T]):

    def __init__(self, maxlen: Optional[int] = None) -> None:
        self.maxlen = maxlen
        self.heap: list[T] = []
        heapq.heapify(self.heap)

    def __len__(self) -> int:
        return len(self.heap)

    @property
    def bounded(self) -> bool:
        return self.maxlen is not None

    @property
    def is_empty(self) -> bool:
        return len(self) == 0

    @property
    def is_full(self) -> bool:
        return self.bounded and len(self) == self.maxlen

    @property
    def min(self) -> Optional[T]:
        return None if self.is_empty else self.heap[0]

    def push(self, item: T) -> Optional[T]:
        if self.is_full:
            return heapq.heapreplace(self.heap, item)
        return heapq.heappush(self.heap, item)

    def pop(self) -> T:
        return heapq.heappop(self.heap)


@dataclass(eq=False)
class QueueingMetrics(Metrics[Q]):

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
        return self.wait_time / max(self.node.current_time, TIME_EPS)

    @property
    def mean_busy_handlers(self) -> float:
        return self.busy_time / max(self.node.current_time, TIME_EPS)

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
class Handler(Generic[T]):
    item: T = field(compare=False)
    next_time: float


class QueueingNode(Node[T]):

    def __init__(self,
                 queue: Queue[T] = Queue(),
                 max_handlers: Optional[int] = None,
                 metrics_type: Type[QueueingMetrics[Q]] = QueueingMetrics,
                 **kwargs: Any) -> None:
        self.metrics: QueueingMetrics = None
        super().__init__(metrics_type=metrics_type, **kwargs)
        self.queue = queue
        self.handlers = MinHeap[Handler[T]](maxlen=max_handlers)
        self.next_time = INF_TIME

    @property
    def num_handlers(self) -> int:
        return len(self.handlers)

    @property
    def queuelen(self) -> int:
        return len(self.queue)

    def start_action(self, item: T) -> None:
        super().start_action(item)
        if self.handlers.is_full:
            if self.queue.is_full:
                self._failure_hook()
            else:
                self.queue.push(item)
        else:
            handler = Handler(item=item, next_time=self._predict_next_time(item=item))
            self._before_add_handler_hook()
            self.handlers.push(handler)
            self.next_time = self.handlers.min.next_time

    def end_action(self) -> None:
        item = self.handlers.pop().item
        if not self.queue.is_empty:
            next_item = self.queue.pop()
            handler = Handler(item=next_item, next_time=self._predict_next_time(item=next_item))
            self._before_add_handler_hook()
            self.handlers.push(handler)

        next_handler = self.handlers.min
        self.next_time = INF_TIME if next_handler is None else next_handler.next_time
        return self._end_action(item)

    def _before_time_update_hook(self, time: float) -> None:
        dtime = time - self.current_time
        self.metrics.wait_time += self.queuelen * dtime
        self.metrics.busy_time += self.num_handlers * dtime

    def _item_out_hook(self) -> None:
        super()._item_out_hook()
        if self.metrics.num_out > 1:
            self.metrics.out_interval += self.current_time - self.metrics.out_time
        self.metrics.out_time = self.current_time

    def _item_in_hook(self) -> None:
        super()._item_in_hook()
        if self.metrics.num_in > 1:
            self.metrics.in_interval += self.current_time - self.metrics.in_time
        self.metrics.in_time = self.current_time

    def _before_add_handler_hook(self) -> None:
        pass

    def _failure_hook(self) -> None:
        self.metrics.num_failures += 1
