from element import Element
from common import INF_TIME


class Model:

    def __init__(self, elements: list[Element]) -> None:
        self.elements = elements

    def simulate(self, end_time: float) -> None:
        current_time = 0

        while current_time < end_time:
            next_time = INF_TIME
            next_elements: list[Element] = []

            for element in self.elements:
                if element.next_time <= next_time:
                    next_time = element.next_time
                    next_elements.append(element)

            current_time = next_time
            for element in self.elements:
                element.current_time = current_time

            for element in next_elements:
                element.end_action()
            self._print_states(current_time)

    def _print_states(self, current_time: float) -> None:
        print(f'{current_time}: {" | ".join([str(element) for element in self.elements])}')
