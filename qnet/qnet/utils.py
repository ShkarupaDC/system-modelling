from functools import partial
from operator import is_not
from typing import Iterable, Optional, TypeVar

T = TypeVar('T')


def filter_none(values: Iterable[Optional[T]]) -> Iterable[T]:
    return filter(partial(is_not, None), values)
