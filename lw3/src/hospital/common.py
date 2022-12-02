from enum import Enum
from dataclasses import dataclass, field

from qnet.common import Item


class SickType(int, Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3

    def __repr__(self) -> str:
        return str(self.value)


@dataclass(eq=False)
class HospitalItem(Item):
    sick_type: SickType = SickType.FIRST
    as_first_sick: bool = field(repr=False, default=False)
