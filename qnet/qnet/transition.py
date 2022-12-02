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
    def connected_nodes(self) -> Iterable['Node[I, NodeMetrics]']:
        return itertools.chain(filter_none(self.next_nodes), super().connected_nodes)

    def add_next_node(self, node: Optional[Node[I, NodeMetrics]], proba: float = 1.0) -> None:
        proba_sum = self.proba_sum + proba
        if proba_sum > 1:
            raise RuntimeError(f'Total probability must be <= 1. Given: {proba_sum}')
        self.proba_sum = proba_sum
        self.next_nodes.append(node)
        self.next_probas.append(proba)

    def _get_next_node(self, _: I) -> Optional[Node[I, NodeMetrics]]:
        if self.proba_sum < 1:
            self.add_next_node(node=None, proba=1 - self.proba_sum)
        return random.choices(self.next_nodes, self.next_probas, k=1)[0]
