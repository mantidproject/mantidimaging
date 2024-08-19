# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING
from collections.abc import Iterator

if TYPE_CHECKING:
    from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint


@dataclass(frozen=True)
class SensibleROI(Iterable):
    __slots__ = ("left", "top", "right", "bottom")
    left: int
    top: int
    right: int
    bottom: int

    def __iter__(self) -> Iterator[int]:
        return iter((self.left, self.top, self.right, self.bottom))

    def __hash__(self):
        return hash((self.left, self.top, self.right, self.bottom))

    def __eq__(self, other):
        if not isinstance(other, SensibleROI):
            return NotImplemented
        return (self.left, self.top, self.right, self.bottom) == (other.left, other.top, other.right, other.bottom)

    @staticmethod
    def from_points(position: CloseEnoughPoint, size: CloseEnoughPoint) -> SensibleROI:
        return SensibleROI(position.x, position.y, position.x + size.x, position.y + size.y)

    @staticmethod
    def from_list(roi: list[int] | list[float]):
        return SensibleROI(int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3]))

    def __str__(self):
        return f"Left: {self.left}, Top: {self.top}, Right: {self.right}, Bottom: {self.bottom}"

    def to_list_string(self) -> str:
        return f"{', '.join([str(e) for e in self])}"

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def area(self) -> int:
        return self.width * self.height

    def overlap(self, other: SensibleROI) -> int:
        intersection_left = max(self.left, other.left)
        intersection_top = max(self.top, other.top)
        intersection_right = min(self.right, other.right)
        intersection_bottom = min(self.bottom, other.bottom)

        if intersection_right > intersection_left and intersection_bottom > intersection_top:
            return (intersection_right - intersection_left) * (intersection_bottom - intersection_top)
        return 0

    def has_significant_overlap(self, other: SensibleROI, threshold: float = 0.5) -> bool:
        overlap_area = self.overlap(other)
        return overlap_area >= threshold * self.area

    def intersection(self, other: SensibleROI) -> SensibleROI:
        intersection_left = max(self.left, other.left)
        intersection_top = max(self.top, other.top)
        intersection_right = min(self.right, other.right)
        intersection_bottom = min(self.bottom, other.bottom)

        if intersection_right > intersection_left and intersection_bottom > intersection_top:
            return SensibleROI(intersection_left, intersection_top, intersection_right, intersection_bottom)
        else:
            return SensibleROI()
