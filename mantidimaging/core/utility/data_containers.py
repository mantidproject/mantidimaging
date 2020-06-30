"""
Containers for data. They don't do much apart from storing the data,
and optionally provide helpful operations.

The biggest benefit is explicitly marking what the value represents (e.g. Degrees),
and helps the type hints to tell you that you might be passing the wrong value (e.g. ScalarCoR to a VectorCoR),
while they're both Float underneath and the value can be used, it just will produce nonsense.
"""
from dataclasses import dataclass


@dataclass
class SingleValue:
    __slots__ = 'value'
    value: float

    def __init__(self, value: float):
        assert isinstance(value, float), f"Value is not float. Actual type:{type(value)}"
        self.value = value

    def __str__(self):
        return f"{self.value}"


@dataclass
class ScalarCoR(SingleValue):
    __slots__ = 'value'
    value: float

    def to_vec(self, detector_width):
        return VectorCoR(detector_width / 2 - self.value)


@dataclass
class VectorCoR:
    __slots__ = 'value'
    value: float

    def to_scalar(self, detector_width):
        return ScalarCoR(detector_width / 2 + self.value)


@dataclass
class Degrees:
    __slots__ = 'value'
    value: float


@dataclass
class Slope:
    __slots__ = 'value'
    value: float
