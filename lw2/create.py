from element import Element


class CreateElement(Element):

    def set_current_time(self, next_time: float) -> None:
        self.current_time = next_time

    def start_action(self) -> None:
        pass

    def end_action(self) -> None:
        self._update_next_time()
        super().end_action()
