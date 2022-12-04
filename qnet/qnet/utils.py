from typing import Iterable, Optional, TypeVar

T = TypeVar('T')


def filter_none(values: Iterable[Optional[T]]) -> Iterable[T]:
    return (value for value in values if value is not None)
