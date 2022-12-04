from typing import Optional, Any

from qnet.node import NM, Node, NodeMetrics
from qnet.transition import ProbaTransitionNode

from .common import CarUnit
from .queueing import RepairQueueingNode


class AfterControlTransitionNode(ProbaTransitionNode[CarUnit, NM]):

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.out_idx: Optional[int] = None
        self.repair_idx: Optional[int] = None

    def add_next_node(self, node: Optional[Node[CarUnit, NodeMetrics]], proba: float = 1) -> None:
        super().add_next_node(node, proba)
        node_idx = self.num_next_nodes - 1
        if node is None:
            self.out_idx = node_idx
        if isinstance(node, RepairQueueingNode):
            self.repair_idx = node_idx

    def _update_repair_proba(self, new_proba: float) -> None:
        proba_shift = self.next_probas[self.repair_idx] - new_proba
        self.next_probas[self.repair_idx] = new_proba
        self.next_probas[self.out_idx] += proba_shift

    def _get_next_node(self, item: CarUnit) -> Optional[Node[CarUnit, NodeMetrics]]:
        assert self.repair_idx is not None and self.out_idx is not None, (self.repair_idx, self.out_idx)
        old_proba = self.next_probas[self.repair_idx]
        new_proba = old_proba**item.num_repairs
        self._update_repair_proba(new_proba)
        next_node = super()._get_next_node(item)
        self._update_repair_proba(old_proba)
        return next_node
