import random
from functools import partial

from create import CreateElement
from process import ProcessElement
from model import Model


def run_simulation() -> None:
    create1 = CreateElement(get_delay=partial(random.expovariate, lambd=1.0 / 0.2))
    process1 = ProcessElement(max_queue_size=10, num_handlers=5, get_delay=partial(random.expovariate, lambd=1.0 / 1.2))
    process2 = ProcessElement(max_queue_size=8, num_handlers=7, get_delay=partial(random.expovariate, lambd=1.0 / 2.0))
    process3 = ProcessElement(max_queue_size=1, num_handlers=2, get_delay=partial(random.expovariate, lambd=1.0 / 1.0))

    create1.add_next_element(process1)
    process1.add_next_element(process2)
    process2.add_next_element(process3)

    model = Model(parent=create1)
    stats = model.simulate(end_time=1000, verbose=False)

    print('Final statistics:')
    for name, element_stats in stats.items():
        print(f'{name}:\n{element_stats}\n')


if __name__ == '__main__':
    run_simulation()
