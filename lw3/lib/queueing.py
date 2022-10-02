from collections import deque
import heapq
from dataclasses import dataclass, field
from typing import Optional, Generic, Any

from .common import INF_TIME, TIME_EPS, T
from .base import Node, Stats


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


@dataclass
class Handler(Generic[T]):
    item: T = field(compare=False)
    next_time: float


class QueueingNode(Node[T]):

    def __init__(self, queue: Queue[T] = Queue(), max_handlers: Optional[int] = None, **kwargs: Any) -> None:
        self.stats: QueueingStats = None
        super().__init__(stats_type=QueueingStats, **kwargs)
        self.queue = queue
        self.handlers = MinHeap[Handler[T]](maxlen=max_handlers)

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
                self.stats.num_failures += 1
            else:
                self.queue.push(item)
        else:
            handler = Handler(item=item, next_time=self._predict_next_time(item=item))
            self.handlers.push(handler)
            self.next_time = self.handlers.min.next_time

    def end_action(self) -> None:
        item = self.handlers.pop().item

        if not self.queue.is_empty:
            next_item = self.queue.pop()
            handler = Handler(item=next_item, next_time=self._predict_next_time(item=next_item))
            self.handlers.push(handler)

        next_handler = self.handlers.min
        self.next_time = INF_TIME if next_handler is None else next_handler.next_time
        return self._end_action_hook(item)

    def update_time(self, time: float) -> None:
        dtime = time - self.current_time
        self.stats.wait_time += self.queuelen * dtime
        self.stats.busy_time += self.num_handlers * dtime
        super().update_time(time)


@dataclass(eq=False)
class QueueingStats(Stats[QueueingNode]):

    wait_time: int = field(init=False, default=0)
    busy_time: int = field(init=False, default=0)
    num_failures: int = field(init=False, default=0)

    @property
    def mean_queue_len(self) -> float:
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
