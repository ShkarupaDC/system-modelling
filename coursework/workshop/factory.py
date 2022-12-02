from qnet.node import NM
from qnet.factory import BaseFactoryNode

from .common import CarUnit


class CarUnitFactoryNode(BaseFactoryNode[CarUnit, NM]):

    def _get_next_item(self) -> CarUnit:
        return CarUnit(id=self.next_id, created_time=self.current_time)
