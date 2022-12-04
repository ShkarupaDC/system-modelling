import random
from abc import abstractmethod
import itertools
from typing import Iterable, Optional, Any, cast

from .common import INF_TIME, I
from .node import NM, Node, NodeMetrics, DelayFn
from .utils import filter_none


class BaseTransitionNode(Node[I, NM]):

    def __init__(self, delay_fn: DelayFn = lambda: 0, **kwargs: Any) -> None:
        super().__init__(delay_fn=delay_fn, **kwargs)
        self.item: Optional[I] = None
        self.next_time = INF_TIME

    @property
    def current_items(self) -> Iterable[I]:
        return filter_none((self.item, ))

    def start_action(self, item: I) -> None:
        super().start_action(item)
        self.item = item
        self.next_time = self._predict_next_time()

    def end_action(self) -> I:
        item = cast(I, self.item)
        self.set_next_node(self._get_next_node(item))
        self._process_item(item)
        self.next_time = INF_TIME
        self.item = None
        return self._end_action(item)

    def reset(self) -> None:
        super().reset()
        self.item = None
        self.next_time = INF_TIME

    def to_dict(self) -> dict[str, Any]:
        return {'item': self.item, 'next_node': self.next_node.name if self.next_node else None}

    def _before_time_update_hook(self, time: float) -> None:
        self.next_node = None
        super()._before_time_update_hook(time)

    def _process_item(self, _: I) -> None:
        pass

    @abstractmethod
    def _get_next_node(self, _: I) -> Optional[Node[I, NodeMetrics]]:
        raise NotImplementedError


class ProbaTransitionNode(BaseTransitionNode[I, NM]):

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.proba_sum: float = 0
        self.next_nodes: list[Optional[Node[I, NodeMetrics]]] = []
        self.next_probas: list[float] = []

    @property
    def rest_proba(self) -> float:
        return 1 - self.proba_sum

    @property
    def num_next_nodes(self) -> int:
        return len(self.next_nodes)

    @property
    def connected_nodes(self) -> Iterable['Node[I, NodeMetrics]']:
        return itertools.chain(filter_none(self.next_nodes), super().connected_nodes)

    def add_next_node(self, node: Optional[Node[I, NodeMetrics]], proba: float = 1.0) -> None:
        proba_sum = self.proba_sum + proba
        assert proba_sum <= 1, 'Total probability must be <= 1. Given: {proba_sum}'
        self.proba_sum = proba_sum
        self.next_nodes.append(node)
        self.next_probas.append(proba)

    def _get_next_node(self, _: I) -> Optional[Node[I, NodeMetrics]]:
        assert self.proba_sum == 1, 'Total probability must be equal to 1'
        return random.choices(self.next_nodes, self.next_probas, k=1)[0]
