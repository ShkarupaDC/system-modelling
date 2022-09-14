from create import CreateElement
from process import ProcessElement
from model import Model


def main() -> None:
    process_element = ProcessElement(max_queue_size=5, name='process1', delay_fn=lambda: 1, delay_kwargs={})
    create_element = CreateElement(name='create1',
                                   delay_fn=lambda: 0.5,
                                   delay_kwargs={},
                                   next_elements=[process_element])
    model = Model(elements=[create_element, process_element])
    model.simulate(end_time=10)


if __name__ == '__main__':
    main()
