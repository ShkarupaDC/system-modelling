from typing import Iterable, Optional, Any

from .base import HospitalItem, SickType

from ..lib.common import INF_TIME
from ..lib.base import Node
from ..lib.queueing import QueueingNode
from ..lib.transition import BaseTransitionNode, ProbaTransitionNode


class AfterTestingTransitionNode(ProbaTransitionNode[HospitalItem]):

    def end_action(self) -> HospitalItem:
        next_node = self._get_next_node()
        if next_node is not None:
            self.item.sick_type = SickType.FIRST
        self.set_next_node(next_node)
        self.next_time = INF_TIME
        return self._end_action_hook(self.item)


class AfterAdmissionTransitionNode(BaseTransitionNode[HospitalItem]):

    def __init__(self, chumber: QueueingNode, reception: QueueingNode, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.chumber = chumber
        self.reception = reception

    @property
    def connected_nodes(self) -> Iterable[Node[HospitalItem]]:
        return [self.chumber, self.reception]

    def _get_next_node(self, item: HospitalItem) -> Optional[QueueingNode]:
        return self.chumber if item.sick_type == SickType.FIRST else self.reception
