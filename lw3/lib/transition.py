import random
from abc import abstractmethod
from typing import Iterable, Optional, Any

from lib.common import INF_TIME, T
from lib.base import Node, DelayFn

NodesProbes = dict[Node[T], float]
NodesAndProbes = tuple[tuple[Node[T]], tuple[float]]


class BaseTransitionNode(Node[T]):

    def __init__(self, delay_fn: DelayFn = lambda: 0, **kwargs: Any) -> None:
        super().__init__(delay_fn=delay_fn, **kwargs)
        self.item: Optional[T] = None
        self.next_time = INF_TIME

    def start_action(self, item: T) -> None:
        super().start_action(item)
        self.item = item
        self.next_time = self._predict_next_time()

    def end_action(self) -> T:
        item = self.item
        self.set_next_node(self._get_next_node(item))
        self._process_item(item)
        self.next_time = INF_TIME
        self.item = None
        return self._end_action(item)

    def reset(self) -> None:
        super().reset()
        self.item = None
        self.next_time = INF_TIME

    def _process_item(self, _: T) -> None:
        pass

    @abstractmethod
    def _get_next_node(self, _: T) -> Optional[Node[T]]:
        raise NotImplementedError


class ProbaTransitionNode(BaseTransitionNode[T]):

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.proba_sum: float = 0
        self.next_nodes: list[Node[T]] = []
        self.next_probas: list[float] = []

    @property
    def connected_nodes(self) -> Iterable['Node[T]']:
        return self.next_nodes

    def add_next_node(self, node: Optional[Node[T]], proba: float = 1.0) -> None:
        proba_sum = self.proba_sum + proba
        if proba_sum > 1:
            raise RuntimeError(f'Total probability must be <= 1. Given: {proba_sum}')
        self.proba_sum = proba_sum
        self.next_nodes.append(node)
        self.next_probas.append(proba)

    def _get_next_node(self, _: T) -> Optional[Node[T]]:
        if self.proba_sum < 1:
            self.add_next_node(node=None, proba=1 - self.proba_sum)
        return random.choices(self.next_nodes, self.next_probas, k=1)[0]
