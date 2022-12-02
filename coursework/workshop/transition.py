from qnet.node import NM
from qnet.transition import ProbaTransitionNode

from .common import CarUnit


class AfterControlTransitionNode(ProbaTransitionNode[CarUnit, NM]):

    def _process_item(self, item: CarUnit) -> None:
        if self.next_node is not None:
            item.returned = True
