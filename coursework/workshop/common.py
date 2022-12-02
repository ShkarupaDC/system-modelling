from dataclasses import dataclass, field

from qnet.common import Item


@dataclass(eq=False)
class CarUnit(Item):
    repair_time: float = field(init=False, repr=False, default=0)
    returned: bool = field(init=False, default=False)
