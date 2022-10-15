import random
import math
from typing import TypeVar

INF_TIME = float('inf')
TIME_EPS = 1e-6

T = TypeVar('T')


def erlang(lambd: float, k: int) -> float:
    product = 1
    for _ in range(k):
        product *= random.random()
    return -1 / lambd * math.log(product)
