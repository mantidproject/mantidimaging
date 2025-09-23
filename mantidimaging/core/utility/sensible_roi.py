# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint


@dataclass(slots=True)
class SensibleROI(Iterable[int]):
    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0

    @staticmethod
    def from_points(position: CloseEnoughPoint, size: CloseEnoughPoint) -> SensibleROI:
        return SensibleROI(position.x, position.y, position.x + size.x, position.y + size.y)

    @staticmethod
    def from_list(roi: list[int] | list[float]) -> SensibleROI:
        return SensibleROI(int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3]))

    def __iter__(self) -> Iterator[int]:
        """
        Allows unpacking the ROI with `*roi`
        :return: Iterable of all ROI parts
        """
        return iter((self.left, self.top, self.right, self.bottom))

    def __str__(self) -> str:
        return f"Left: {self.left}, Top: {self.top}, Right: {self.right}, Bottom: {self.bottom}"

    def to_list_string(self) -> str:
        return f"{', '.join([str(e) for e in self])}"

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


class ROIBinner:

    def __init__(self, roi: SensibleROI, step_size: int, bin_size: int):
        self.roi = roi
        self.step_size = step_size
        self.bin_size = bin_size

        self.left_indexes = range(self.roi.left, self.roi.right - self.bin_size + 1, self.step_size)
        self.top_indexes = range(self.roi.top, self.roi.bottom - self.bin_size + 1, self.step_size)

    def lengths(self) -> tuple[int, int]:
        return len(self.left_indexes), len(self.top_indexes)

    def get_sub_roi(self, i: int, j: int) -> SensibleROI:
        left = self.left_indexes[i]
        top = self.top_indexes[j]
        return SensibleROI(left, top, left + self.bin_size, top + self.bin_size)
