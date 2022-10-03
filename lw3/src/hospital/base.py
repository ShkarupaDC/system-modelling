from enum import Enum
from dataclasses import dataclass

from ..lib.base import Item


class SickType(int, Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3


@dataclass(eq=False)
class HospitalItem(Item):
    sick_type: SickType = SickType.FIRST
