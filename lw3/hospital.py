import random
from functools import partial

from src.lib.common import erlang
from src.lib.queueing import QueueingNode
from src.lib.model import Model

from src.hospital import (HospitalItem, SickType, HospitalFactoryNode, EmergencyQueue, TestingTransitionNode,
                          EmergencyTransitionNode, HospitalLogger)


def run_simulation() -> None:
    # Processing nodes
    sick_type_probas = {SickType.FIRST: 0.5, SickType.SECOND: 0.1, SickType.THIRD: 0.4}
    incoming_sick_people = HospitalFactoryNode(name='1. Sick people',
                                               probas=sick_type_probas,
                                               delay_fn=partial(random.expovariate, lambd=1.0 / 15))
    at_emergency_mean = {SickType.FIRST: 15, SickType.SECOND: 40, SickType.THIRD: 30}
    at_emergency = QueueingNode[HospitalItem](
        name='2. At Emergency',
        queue=EmergencyQueue(),
        max_handlers=2,
        delay_fn=lambda item: random.expovariate(lambd=1.0 / at_emergency_mean[item.sick_type]))

    to_chumber = QueueingNode[HospitalItem](name='4. To chumber',
                                            max_handlers=3,
                                            delay_fn=partial(random.uniform, a=3, b=8))
    to_reception = QueueingNode[HospitalItem](name='5. To reception', delay_fn=partial(random.uniform, a=2, b=5))
    at_reception = QueueingNode[HospitalItem](name='6. At reception', delay_fn=partial(erlang, lambd=3 / 4.5, k=3))
    on_testing = QueueingNode[HospitalItem](name='7. On Testing',
                                            max_handlers=2,
                                            delay_fn=partial(erlang, lambd=2 / 4, k=2))

    # Connections
    incoming_sick_people.set_next_node(at_emergency)
    emergency_transition = EmergencyTransitionNode(name='3. Chamber vs Reception',
                                                   chumber=to_chumber,
                                                   reception=to_reception)
    at_emergency.set_next_node(emergency_transition)
    to_reception.set_next_node(at_reception)
    at_reception.set_next_node(on_testing)
    testing_transition = TestingTransitionNode(name='8. After Testing', nodes_probas={at_emergency: 0.2})
    on_testing.set_next_node(testing_transition)

    model = Model.from_factory(incoming_sick_people, logger=HospitalLogger())
    model.simulate(end_time=100000, verbose=False)


if __name__ == '__main__':
    run_simulation()
