import random
from dataclasses import dataclass


@dataclass(eq=False)
class Point:
    x: float
    a: float


def empirical(points: list[Point]) -> float:
    a_uniform = random.uniform(0, 1)
    start, end = None, None

    for start, end in zip(points, points[1:]):
        if start.a <= a_uniform <= end.a:
            return start.x + (end.x - start.x) / (end.a - start.a) * (a_uniform - start.a)

    raise RuntimeError('Points are selected incorrectly')


if __name__ == '__main__':
    points = [Point(x=0, a=0), Point(x=2, a=0.3), Point(x=4, a=0.7), Point(x=6, a=0.9), Point(x=10, a=1.0)]
    print(empirical(points))
