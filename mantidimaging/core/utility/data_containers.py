# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
Containers for data. They don't do much apart from storing the data,
and optionally provide helpful operations.

The biggest benefit is explicitly marking what the value represents (e.g. Degrees),
and helps the type hints to tell you that you might be passing the wrong value (e.g. ScalarCoR to a VectorCoR),
while they're both Float underneath and the value can be used, it just will produce nonsense.
"""
from collections import namedtuple
from dataclasses import dataclass
from typing import Optional

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

    def __eq__(self, other):
        if isinstance(other, SingleValue):
            return self.value == other.value
        else:
            return self == other

    def __abs__(self):
        return abs(self.value)

    def __sub__(self, other: 'SingleValue'):
        assert isinstance(other, SingleValue), "Can only compare against other `SingleValue`s"
        return self.value - other.value


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

    def __str__(self):
        return f"{self.value}°"


@dataclass
class Slope(SingleValue):
    __slots__ = 'value'
    value: float


@dataclass
class ProjectionAngles(SingleValue):
    __slots__ = 'value'
    value: numpy.ndarray


@dataclass
class Counts(SingleValue):
    __slots__ = 'value'
    value: numpy.ndarray


@dataclass
class Micron(SingleValue):
    __slots__ = 'value'
    value: int


@dataclass
class ReconstructionParameters:
    algorithm: str
    filter_name: str
    num_iter: int = 1
    cor: Optional[ScalarCoR] = None
    tilt: Optional[Degrees] = None
    pixel_size: float = 0.0
    alpha: float = 0.0
    max_projection_angle: float = 360.0

    def to_dict(self) -> dict:
        return {
            'algorithm': self.algorithm,
            'filter_name': self.filter_name,
            'num_iter': self.num_iter,
            'cor': str(self.cor),
            'tilt': str(self.tilt),
            'pixel_size': self.pixel_size,
            'alpha': self.alpha
        }


Indices = namedtuple('Indices', ['start', 'end', 'step'])


@dataclass
class ImageParameters:
    input_path: str
    format: str
    prefix: str
    indices: Optional[Indices] = None
    log_file: Optional[str] = None


class LoadingParameters:
    sample: ImageParameters
    flat_before: Optional[ImageParameters] = None
    flat_after: Optional[ImageParameters] = None
    dark_before: Optional[ImageParameters] = None
    dark_after: Optional[ImageParameters] = None
    proj_180deg: Optional[ImageParameters] = None

    pixel_size: int
    name: str
    dtype: str
    sinograms: bool
