from numbers import Number


class MeanMeter:

    def __init__(self) -> None:
        self.sum = 0
        self.count = 0

    @property
    def mean(self) -> float:
        return self.sum / max(self.count, 1)

    def update(self, value: Number) -> None:
        self.sum += value
        self.count += 1
