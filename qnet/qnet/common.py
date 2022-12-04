from collections import deque
import heapq
import itertools
import inspect
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields, _MISSING_TYPE
from typing import (TypeVar, Generic, Optional, Iterable, Callable, SupportsFloat, Protocol, Union, Any, cast,
                    runtime_checkable)

INF_TIME = float('inf')
TIME_EPS = 1e-6

I = TypeVar('I', bound='Item')
M = TypeVar('M', bound='Metrics')
T = TypeVar('T')


@runtime_checkable
class SupportsDict(Protocol):

    def to_dict(self) -> dict[str, Any]:
        ...


class ActionType(str, Enum):
    IN = 'in'
    OUT = 'out'


@dataclass(eq=False)
class ActionRecord(SupportsDict, Generic[T]):
    node: T
    action_type: ActionType
    time: float

    def to_dict(self) -> dict[str, Any]:
        return {'node': self.node, 'action_type': self.action_type, 'time': self.time}


@dataclass(eq=False)
class Item(SupportsDict):
    id: str
    created_time: float = field(repr=False)
    current_time: float = field(init=False, repr=False)
    processed: bool = field(init=False, repr=False, default=False)
    history: list[ActionRecord] = field(init=False, repr=False, default_factory=list)

    def __post_init__(self) -> None:
        self.current_time = self.created_time

    @property
    def released_time(self) -> Optional[float]:
        return self.current_time if self.processed else None

    @property
    def time_in_system(self) -> float:
        return self.current_time - self.created_time

    def to_dict(self) -> dict[str, Any]:
        return {'id': self.id}


@dataclass(eq=False)
class Metrics(Protocol):
    passed_time: float = field(init=False, default=0)

    def to_dict(self) -> dict[str, Any]:
        metrics_dict = {
            name: getattr(self, name)
            for name, _ in inspect.getmembers(type(self),
                                              lambda value: isinstance(value, property) and value.fget is not None)
        }
        return metrics_dict

    def reset(self) -> None:
        for param in fields(self):
            if not isinstance(param.default, _MISSING_TYPE):
                default = param.default
            elif not isinstance(param.default_factory, _MISSING_TYPE):
                default = param.default_factory()
            else:
                continue
            setattr(self, param.name, default)


class BoundedCollection(ABC, SupportsDict, Generic[T]):

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def bounded(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def maxlen(self) -> Optional[int]:
        raise NotImplementedError

    @property
    @abstractmethod
    def data(self) -> Iterable[T]:
        raise NotImplementedError

    @property
    def is_empty(self) -> bool:
        return len(self) == 0

    @property
    def is_full(self) -> bool:
        return self.bounded and len(self) == self.maxlen

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def push(self, item: T) -> Optional[T]:
        raise NotImplementedError

    @abstractmethod
    def pop(self) -> T:
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        return {'items': list(self.data), 'max_size': self.maxlen}


class Queue(BoundedCollection[T]):

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
    def data(self) -> Iterable[T]:
        return self.queue

    def clear(self) -> None:
        self.queue.clear()

    def push(self, item: T) -> Optional[T]:  # pylint: disable=useless-return
        self.queue.append(item)
        return None

    def pop(self) -> T:
        return self.queue.popleft()


class LIFOQueue(Queue[T]):

    def pop(self) -> T:
        return self.queue.pop()


class MinHeap(BoundedCollection[T]):

    def __init__(self, maxlen: Optional[int] = None) -> None:
        self._maxlen = maxlen
        self.heap: list[T] = []
        heapq.heapify(self.heap)

    def __len__(self) -> int:
        return len(self.heap)

    @property
    def bounded(self) -> bool:
        return self.maxlen is not None

    @property
    def maxlen(self) -> Optional[int]:
        return self._maxlen

    @property
    def data(self) -> Iterable[T]:
        return self.heap

    @property
    def min(self) -> Optional[T]:
        return None if self.is_empty else self.heap[0]

    def clear(self) -> None:
        self.heap.clear()

    def push(self, item: T) -> Optional[T]:
        if self.is_full:
            return heapq.heapreplace(self.heap, item)
        heapq.heappush(self.heap, item)
        return None

    def pop(self) -> T:
        return heapq.heappop(self.heap)


PriorityTuple = Union[tuple[SupportsFloat, T], tuple[SupportsFloat, int, T]]


class PriorityQueue(MinHeap[T]):

    def __init__(self, priority_fn: Callable[[T], SupportsFloat], fifo: Optional[bool] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.fifo = fifo
        self.priority_fn = priority_fn

        if self.fifo is not None:
            self.counter = itertools.count()

    @property
    def data(self) -> Iterable[T]:
        return (cast(PriorityTuple[T], item)[-1] for item in self.heap)

    def push(self, item: T) -> Optional[T]:
        priority = self.priority_fn(item)
        if self.fifo is None:
            element: PriorityTuple[T] = (priority, item)
        else:
            count = next(self.counter)
            element = (priority, count if self.fifo else -count, item)
        return super().push(cast(T, element))

    def pop(self) -> T:
        return cast(PriorityTuple[T], super().pop())[-1]
