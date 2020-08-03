"""
Containers for data. They don't do much apart from storing the data,
and optionally provide helpful operations.

The biggest benefit is explicitly marking what the value represents (e.g. Degrees),
and helps the type hints to tell you that you might be passing the wrong value (e.g. ScalarCoR to a VectorCoR),
while they're both Float underneath and the value can be used, it just will produce nonsense.
"""
from dataclasses import dataclass

import numpy


@dataclass
class SingleValue:
    __slots__ = 'value'
    value: float

    def __init__(self, value: float):
        assert isinstance(value, float), f"Value is not float. Actual type:{type(value)}"
        self.value = value

    def __str__(self):
        return f"{self.value}"

    def __eq__(self, other: 'SingleValue'):
        assert isinstance(other, SingleValue), "Can only compare against other `SingleValue`s"
        return self.value == other.value


@dataclass
class ScalarCoR(SingleValue):
    __slots__ = 'value'
    value: float

    def to_vec(self, detector_width):
        return VectorCoR(detector_width / 2 - self.value)


@dataclass
class VectorCoR(SingleValue):
    __slots__ = 'value'
    value: float

    def to_scalar(self, detector_width):
        return ScalarCoR(detector_width / 2 + self.value)


@dataclass
class Degrees(SingleValue):
    __slots__ = 'value'
    value: float


@dataclass
class Slope(SingleValue):
    __slots__ = 'value'
    value: float


@dataclass
class ProjectionAngles(SingleValue):
    __slots__ = 'value'
    value: numpy.ndarray


@dataclass
class ReconstructionParameters:
    algorithm: str
    filter_name: str
    num_iter: int = 1
