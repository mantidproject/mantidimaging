# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING
from collections.abc import Iterator

if TYPE_CHECKING:
    from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint


@dataclass
class SensibleROI(Iterable):
    __slots__ = ("left", "top", "right", "bottom")
    left: int
    top: int
    right: int
    bottom: int

    def __init__(self, left=0, top=0, right=0, bottom=0):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    @staticmethod
    def from_points(position: CloseEnoughPoint, size: CloseEnoughPoint) -> SensibleROI:
        return SensibleROI(position.x, position.y, position.x + size.x, position.y + size.y)

    @staticmethod
    def from_list(roi: list[int] | list[float]):
        return SensibleROI(int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3]))

    def __iter__(self) -> Iterator[int]:
        """
        Allows unpacking the ROI with `*roi`
        :return: Iterable of all ROI parts
        """
        return iter((self.left, self.top, self.right, self.bottom))

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
        """
        Calculate the area of the ROI.
        """
        return self.width * self.height

    def intersection(self, other: SensibleROI) -> SensibleROI:
        """
        Calculate the intersection of two ROIs.
        """
        intersection_left = max(self.left, other.left)
        intersection_top = max(self.top, other.top)
        intersection_right = min(self.right, other.right)
        intersection_bottom = min(self.bottom, other.bottom)

        if intersection_right > intersection_left and intersection_bottom > intersection_top:
            return SensibleROI(intersection_left, intersection_top, intersection_right, intersection_bottom)
        else:
            return SensibleROI(0, 0, 0, 0)  # No intersection

    @property
    def intersection_area(self, other: SensibleROI) -> int:
        """
        Calculate the area of the intersection with another ROI.
        """
        intersection = self.intersection(other)
        return intersection.area

    def overlap_percentage(self, other: SensibleROI) -> float:
        """
        Calculate the percentage of overlap with another ROI.
        """
        intersection_area = self.intersection_area(other)
        if self.area == 0:
            return 0
        return intersection_area / self.area
