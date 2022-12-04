from dataclasses import dataclass, field

from qnet.common import Item


@dataclass(eq=False)
class CarUnit(Item):
    repair_time: float = field(init=False, repr=False, default=0)  # last
    num_repairs: int = field(init=False, repr=False, default=0)
    repair_wait_time: float = field(init=False, repr=False, default=0)  # total

    def __lt__(self, other: 'CarUnit') -> bool:
        if self.num_repairs >= 1 and other.num_repairs >= 1:
            return self.time_in_system > other.time_in_system
        return self.repair_time < other.repair_time
