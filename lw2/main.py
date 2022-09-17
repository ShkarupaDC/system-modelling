import random
from functools import partial

from create import CreateElement
from process import ProcessElement
from model import Model


def run_simulation() -> None:
    create1 = CreateElement(get_delay=partial(random.uniform, a=0.2, b=0.5))
    process1 = ProcessElement(max_queue_size=5, num_handlers=2, get_delay=partial(random.gauss, mu=1.0, sigma=0.05))
    process2 = ProcessElement(max_queue_size=5, get_delay=partial(random.gauss, mu=1.0, sigma=0.05))
    process3 = ProcessElement(max_queue_size=5, get_delay=partial(random.gauss, mu=1.0, sigma=0.05))

    create1.add_next_element(process1)
    process1.add_next_element(process2)
    process2.add_next_element(process3)

    model = Model(parent=create1)
    stats = model.simulate(end_time=5, verbose=True)

    print('Final statistics:')
    for name, element_stats in stats.items():
        print(f'{name}:\n{element_stats}\n')


if __name__ == '__main__':
    run_simulation()
