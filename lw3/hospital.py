import random
from functools import partial

from src.lib.common import erlang
from src.lib.queueing import QueueingNode
from src.lib.model import Model

from src.hospital import (HospitalItem, SickType, HospitalFactoryNode, EmergencyQueue, TestingTransitionNode,
                          EmergencyTransitionNode)


def run_simulation() -> None:
    # Processing nodes
    sick_type_probas = {SickType.FIRST: 0.5, SickType.SECOND: 0.1, SickType.THIRD: 0.4}
    incoming_sick_people = HospitalFactoryNode(probas=sick_type_probas,
                                               delay_fn=partial(random.expovariate, lambd=1.0 / 15))
    at_emergency_mean = {SickType.FIRST: 15, SickType.SECOND: 40, SickType.THIRD: 30}
    at_emergency = QueueingNode[HospitalItem](
        queue=EmergencyQueue(),
        max_handlers=2,
        delay_fn=lambda item: random.expovariate(lambd=at_emergency_mean[item.sick_type]))

    to_chumber = QueueingNode[HospitalItem](max_handlers=3, delay_fn=partial(random.uniform, a=3, b=8))
    to_reception = QueueingNode[HospitalItem](delay_fn=partial(random.uniform, a=2, b=5))
    at_reception = QueueingNode[HospitalItem](delay_fn=partial(erlang, mean=4.5, k=3))
    on_testing = QueueingNode[HospitalItem](max_handlers=2, delay_fn=partial(erlang, mean=4, k=2))

    # Connections
    incoming_sick_people.set_next_node(at_emergency)
    emergency_transition = EmergencyTransitionNode(chumber=to_chumber, reception=to_reception)
    at_emergency.set_next_node(emergency_transition)
    to_reception.set_next_node(at_reception)
    at_reception.set_next_node(on_testing)
    testing_transition = TestingTransitionNode(nodes_probas={at_emergency: 0})
    on_testing.set_next_node(testing_transition)

    model = Model.from_factory(incoming_sick_people)
    model.simulate(end_time=10, verbose=True)


if __name__ == '__main__':
    run_simulation()
