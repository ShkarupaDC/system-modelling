from dataclasses import dataclass, field

from lib.base import Item


@dataclass(eq=False)
class CarUnit(Item):
    repair_time: float = field(init=False, default=0)
    returned: bool = field(init=False, default=False)

    def __lt__(self, other: 'CarUnit') -> bool:
        if self.returned and other.returned:
            return self.time_in_system < self.time_in_system
        if self.returned or other.returned:
            return self.returned
        return self.repair_time < other.repair_time
