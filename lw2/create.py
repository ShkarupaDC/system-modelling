from element import Element


class CreateElement(Element):

    def start_action(self) -> None:
        pass

    def end_action(self) -> None:
        self._update_next_time()
        super().end_action()
