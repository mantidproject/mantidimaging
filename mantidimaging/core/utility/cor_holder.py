from dataclasses import dataclass


@dataclass
class ScalarCoR:
    __slots__ = 'value'
    value: float

    def to_vec(self, detector_width):
        return detector_width / 2 - self.value


@dataclass
class VectorCoR:
    __slots__ = 'value'
    value: float

    def to_scalar(self, detector_width):
        return detector_width / 2 + self.value
