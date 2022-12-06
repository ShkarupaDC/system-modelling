import random
from functools import partial

from src.hospital import (HospitalItem, SickType, HospitalFactoryNode, HospitalModelMetrics, TestingTransitionNode,
                          EmergencyTransitionNode)

from qnet.common import PriorityQueue, Queue
from qnet.node import NodeMetrics
from qnet.dist import erlang
from qnet.queueing import QueueingNode, QueueingMetrics, ChannelPool
from qnet.logger import CLILogger
from qnet.model import Model, Nodes


def _priority_fn(item: HospitalItem) -> int:
    return int(item.sick_type != SickType.FIRST and not item.as_first_sick)


def run_simulation() -> None:
    # Processing nodes
    sick_type_probas = {SickType.FIRST: 0.5, SickType.SECOND: 0.1, SickType.THIRD: 0.4}
    incoming_sick_people = HospitalFactoryNode[NodeMetrics](name='1_sick_people',
                                                            probas=sick_type_probas,
                                                            metrics=NodeMetrics(),
                                                            delay_fn=partial(random.expovariate, lambd=1.0 / 15))
    at_emergency_mean = {SickType.FIRST: 15, SickType.SECOND: 40, SickType.THIRD: 30}
    at_emergency = QueueingNode[HospitalItem, QueueingMetrics](
        name='2_at_emergency',
        queue=PriorityQueue[HospitalItem](priority_fn=_priority_fn, fifo=True),
        metrics=QueueingMetrics(),
        channel_pool=ChannelPool(max_channels=2),
        delay_fn=lambda item: random.expovariate(lambd=1.0 / at_emergency_mean[item.sick_type]))
    emergency_transition = EmergencyTransitionNode[NodeMetrics](name='3_chamber_vs_reception', metrics=NodeMetrics())
    to_chumber = QueueingNode[HospitalItem, QueueingMetrics](name='4_to_chumber',
                                                             queue=Queue[HospitalItem](),
                                                             metrics=QueueingMetrics(),
                                                             channel_pool=ChannelPool(max_channels=3),
                                                             delay_fn=partial(random.uniform, a=3, b=8))
    to_reception = QueueingNode[HospitalItem, QueueingMetrics](name='5_to_reception',
                                                               queue=Queue[HospitalItem](),
                                                               metrics=QueueingMetrics(),
                                                               channel_pool=ChannelPool(),
                                                               delay_fn=partial(random.uniform, a=2, b=5))
    at_reception = QueueingNode[HospitalItem, QueueingMetrics](name='6_at_reception',
                                                               queue=Queue[HospitalItem](),
                                                               metrics=QueueingMetrics(),
                                                               channel_pool=ChannelPool(),
                                                               delay_fn=partial(erlang, lambd=3 / 4.5, k=3))
    on_testing = QueueingNode[HospitalItem, QueueingMetrics](name='7_on_testing',
                                                             queue=Queue[HospitalItem](),
                                                             metrics=QueueingMetrics(),
                                                             channel_pool=ChannelPool(max_channels=2),
                                                             delay_fn=partial(erlang, lambd=2 / 4, k=2))
    testing_transition = TestingTransitionNode[NodeMetrics](name='8_after_testing', metrics=NodeMetrics())

    # Connections
    incoming_sick_people.set_next_node(at_emergency)
    at_emergency.set_next_node(emergency_transition)
    emergency_transition.set_next_nodes(chumber=to_chumber, reception=to_reception)
    to_reception.set_next_node(at_reception)
    at_reception.set_next_node(on_testing)
    on_testing.set_next_node(testing_transition)
    testing_transition.add_next_node(at_emergency, proba=0.2)
    testing_transition.add_next_node(None, proba=testing_transition.rest_proba)

    model = Model(nodes=Nodes[HospitalItem].from_node_tree_root(incoming_sick_people),
                  logger=CLILogger[HospitalItem](),
                  metrics=HospitalModelMetrics())
    model.simulate(end_time=100000)


if __name__ == '__main__':
    run_simulation()
