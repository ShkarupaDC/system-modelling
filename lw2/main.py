import random
from functools import partial

from create import CreateElement
from process import ProcessElement
from model import Model


def main() -> None:
    process_element = ProcessElement(max_queue_size=5,
                                     name='process1',
                                     get_delay=partial(random.gauss, mu=1.0, sigma=0.05))
    create_element = CreateElement(name='create1',
                                   get_delay=partial(random.uniform, a=0.5, b=1.5),
                                   next_elements=[process_element])

    model = Model(elements=[create_element, process_element])
    stats = model.simulate(end_time=5, verbose=True)

    print('Final statistics:')
    print('\n'.join(map(str, stats)))


if __name__ == '__main__':
    main()
