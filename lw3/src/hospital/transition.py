from typing import Iterable, Optional, Any

from lib.base import Node
from lib.queueing import QueueingNode
from lib.transition import BaseTransitionNode, ProbaTransitionNode

from .base import HospitalItem, SickType


class TestingTransitionNode(ProbaTransitionNode[HospitalItem]):

    def _process_item(self, item: HospitalItem) -> None:
        if self.next_node is not None:
            item.as_first_sick = True


class EmergencyTransitionNode(BaseTransitionNode[HospitalItem]):

    def __init__(self, chumber: QueueingNode, reception: QueueingNode, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.chumber = chumber
        self.reception = reception

    @property
    def connected_nodes(self) -> Iterable[Node[HospitalItem]]:
        return [self.chumber, self.reception]

    def _get_next_node(self, item: HospitalItem) -> Optional[QueueingNode]:
        return self.chumber if item.sick_type == SickType.FIRST or item.as_first_sick else self.reception
