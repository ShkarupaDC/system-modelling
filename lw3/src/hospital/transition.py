import itertools
from typing import Iterable, Optional, Any

from qnet.node import NM, Node, NodeMetrics
from qnet.queueing import QueueingMetrics, QueueingNode
from qnet.transition import BaseTransitionNode, ProbaTransitionNode

from .common import HospitalItem, SickType

HospitalQueueingNode = QueueingNode[HospitalItem, QueueingMetrics]


class TestingTransitionNode(ProbaTransitionNode[HospitalItem, NM]):

    def _process_item(self, item: HospitalItem) -> None:
        if self.next_node is not None:
            item.as_first_sick = True


class EmergencyTransitionNode(BaseTransitionNode[HospitalItem, NM]):

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.chumber: HospitalQueueingNode = None
        self.reception: HospitalQueueingNode = None

    @property
    def connected_nodes(self) -> Iterable['Node[HospitalItem, NodeMetrics]']:
        return itertools.chain((self.chumber, self.reception), super().connected_nodes)

    def set_next_nodes(self, chumber: HospitalQueueingNode, reception: HospitalQueueingNode) -> None:
        self.chumber = chumber
        self.reception = reception

    def _get_next_node(self, item: HospitalItem) -> Optional[Node[HospitalItem, NodeMetrics]]:
        assert self.chumber is not None and self.reception is not None
        return self.chumber if item.sick_type == SickType.FIRST or item.as_first_sick else self.reception
