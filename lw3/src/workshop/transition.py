from qnet.transition import ProbaTransitionNode

from .base import CarUnit


class AfterControlTransition(ProbaTransitionNode[CarUnit]):

    def _process_item(self, item: CarUnit) -> None:
        if self.next_node is not None:
            item.returned = True
