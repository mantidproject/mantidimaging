# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
Containers for data. They don't do much apart from storing the data,
and optionally provide helpful operations.

The biggest benefit is explicitly marking what the value represents (e.g. Degrees),
and helps the type hints to tell you that you might be passing the wrong value (e.g. ScalarCoR to a VectorCoR),
while they're both Float underneath and the value can be used, it just will produce nonsense.
"""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Any, List, Optional, NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
    import numpy


@dataclass
class SingleValue:
    __slots__ = 'value'
    value: Any

    def __init__(self, value: Any):
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
    non_negative: bool = False
    max_projection_angle: float = 360.0
    beam_hardening_coefs: Optional[List[float]] = None
    stochastic: bool = False
    projections_per_subset: int = 50
    regularisation_percent: int = 30

    def to_dict(self) -> dict:
        return {
            'algorithm': self.algorithm,
            'filter_name': self.filter_name,
            'num_iter': self.num_iter,
            'cor': str(self.cor),
            'tilt': str(self.tilt),
            'pixel_size': self.pixel_size,
            'alpha': self.alpha,
            'stochastic': self.stochastic,
            'projections_per_subset': self.projections_per_subset,
            'regularisation_percent': self.regularisation_percent,
        }


Indices = NamedTuple("Indices", [("start", int), ("end", int), ("step", int)])


class FILE_TYPES(Enum):
    SAMPLE = ("Sample", "", "sample")
    FLAT_BEFORE = ("Flat", "Before", "images")
    FLAT_AFTER = ("Flat", "After", "images")
    DARK_BEFORE = ("Dark", "Before", "images")
    DARK_AFTER = ("Dark", "After", "images")
    PROJ_180 = ("180 degree", "", "180")
    SAMPLE_LOG = ("Sample Log", "", "log")
    FLAT_BEFORE_LOG = ("Flat Before Log", "", "log")
    FLAT_AFTER_LOG = ("Flat After Log", "", "log")

    def __init__(self, tname: str, suffix: str, mode: str) -> None:
        self.tname = tname
        self.suffix = suffix
        self.mode = mode

    @property
    def fname(self) -> str:
        return (self.tname + " " + self.suffix).strip()


log_for_file_type = {
    FILE_TYPES.SAMPLE: FILE_TYPES.SAMPLE_LOG,
    FILE_TYPES.FLAT_BEFORE: FILE_TYPES.FLAT_BEFORE_LOG,
    FILE_TYPES.FLAT_AFTER: FILE_TYPES.FLAT_AFTER_LOG,
}
