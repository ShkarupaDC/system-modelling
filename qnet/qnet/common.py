import random
import math
import bisect
from dataclasses import dataclass
from typing import TypeVar, Generic, Sequence, Callable

INF_TIME = float('inf')
TIME_EPS = 1e-6

T = TypeVar('T')
V = TypeVar('V')


def erlang(lambd: float, k: int) -> float:
    product = 1
    for _ in range(k):
        product *= random.random()
    return -1 / lambd * math.log(product)


class KeyWapper(Generic[T, V]):

    def __init__(self, sequence: Sequence[T], key: Callable[[T], V]) -> None:
        self.key = key
        self.sequence = sequence

    def __len__(self) -> int:
        return len(self.sequence)

    def __getitem__(self, idx: int) -> V:
        return self.key(self.sequence[idx])


@dataclass(eq=False)
class EmpiricalPoint:
    value: float
    cum_proba: float


def empirical(points: list[EmpiricalPoint]) -> float:
    num_points = len(points)

    assert num_points >= 2 and points[0].cum_proba == 0 and points[-1].cum_proba == 1, points
    proba = random.uniform(0, 1)

    start_idx = bisect.bisect_right(KeyWapper(points, key=lambda point: point.cum_proba), proba) - 1
    end_idx = min(start_idx + 1, num_points - 1)

    start, end = points[start_idx], points[end_idx]
    return start.value + (end.value - start.value) / (end.cum_proba - start.cum_proba) * (proba - start.cum_proba)
