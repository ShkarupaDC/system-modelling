import random
from abc import abstractmethod
from typing import Iterable, Optional, Any

from .common import INF_TIME, T
from .base import Node, DelayFn

NodesProbes = dict[Node[T], float]


class BaseTransitionNode(Node[T]):

    def __init__(self, get_delay: DelayFn = lambda: 0, **kwargs: Any) -> None:
        super().__init__(get_delay=get_delay, **kwargs)
        self.item: T = None
        self.next_time = INF_TIME

    def start_action(self, item: T) -> None:
        super().start_action(item)
        self.item = item
        self.next_time = self._predict_next_time()

    def end_action(self) -> T:
        self.set_next_node(self._get_next_node(item=self.item))
        self.next_time = INF_TIME
        return self._end_action_hook(self.item)

    @abstractmethod
    def _get_next_node(self, item: T) -> Optional[Node[T]]:
        raise NotImplementedError


class ProbaTransitionNode(BaseTransitionNode[T]):

    def __init__(self, nodes_probas: NodesProbes, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.nodes_probas = self._process_input(nodes_probas)

    @staticmethod
    def _process_input(nodes_probas: NodesProbes) -> NodesProbes:
        proba_sum = sum(nodes_probas.keys())
        if proba_sum > 1:
            raise RuntimeError(f'Total probability must be <= 1. Given: {proba_sum}')
        if proba_sum < 1:
            nodes_probas[None] = 1 - proba_sum
        return nodes_probas

    @property
    def connected_nodes(self) -> Iterable['Node[T]']:
        return self.nodes_probas.keys()

    def _get_next_node(self, _: T) -> Optional[Node[T]]:
        return random.choices(self.nodes_probas.keys(), self.nodes_probas.values(), k=1)[0]
