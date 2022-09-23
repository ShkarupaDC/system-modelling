from element import Element, Stats
from common import INF_TIME
from process import TIME_EPS


class Model:

    def __init__(self, parent: Element) -> None:
        self._extract_elements(parent)

    def _extract_elements(self, parent: Element) -> list[Element]:
        elements: set[Element] = set()

        def process_element(parent: Element) -> None:
            elements.add(parent)
            for element in parent.next_elements:
                if element not in elements:
                    process_element(element)

        process_element(parent)
        self.elements = list(elements)

    def simulate(self, end_time: float, verbose: bool = False) -> dict[str, Stats]:
        current_time = 0

        while current_time < end_time:
            next_time = INF_TIME
            for element in self.elements:
                if element.next_time < next_time:
                    next_time = element.next_time
            current_time = next_time

            for element in self.elements:
                element.set_current_time(current_time)

            updated_names: list[str] = []
            for element in self.elements:
                if abs(next_time - element.next_time) < TIME_EPS:
                    element.end_action()
                    updated_names.append(element.name)

            if verbose:
                self._print_states(current_time, updated_names)

        return {element.name: element.stats for element in self.elements}

    def _print_states(self, current_time: float, updated_names: list[str]) -> None:
        states_repr = ' | '.join([str(element) for element in self.elements])
        print(f'{current_time:.5f}: [Updated: {updated_names}]. States: {states_repr}\n')
