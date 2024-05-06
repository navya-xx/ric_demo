import abc


class DiscreteLED(abc.ABC):
    state: int

    def __init__(self):
        pass

    def set(self, state: int):
        pass

    def toggle(self):
        pass

    def blink(self, times: int, time: float):
        pass

    @abc.abstractmethod
    def _set(self):
        ...


class RGB_LED(abc.ABC):
    color: list
    state: int

    def __init__(self):
        pass

    def set(self, state, color):
        pass

    @abc.abstractmethod
    def _set(self):
        ...


class RGB_LED_Strand(abc.ABC):
    led: list[RGB_LED]
    N: int

    def __init__(self, N: int):
        self.N = N
        self.led = [RGB_LED()]*N

    @abc.abstractmethod
    def _set(self):
        ...

