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
        self._roi = roi
        self._step_size = step_size
        self._bin_size = bin_size

        if step_size < 1:
            raise ValueError("ROIBinner step_size must greater than zero")

        self.left_indexes = range(roi.left, roi.right - bin_size + 1, step_size)
        self.top_indexes = range(roi.top, roi.bottom - bin_size + 1, step_size)

    def lengths(self) -> tuple[int, int]:
        return len(self.left_indexes), len(self.top_indexes)

    def get_sub_roi(self, i: int, j: int) -> SensibleROI:
        left = self.left_indexes[i]
        top = self.top_indexes[j]
        return SensibleROI(left, top, left + self.bin_size, top + self.bin_size)

    @property
    def roi(self) -> SensibleROI:
        return self._roi

    @property
    def step_size(self) -> int:
        return self._step_size

    @property
    def bin_size(self) -> int:
        return self._bin_size

    def is_valid(self) -> tuple[bool, str]:
        """
        Validates that the bin_size and step_size are compatible with aech other the roi dimensions
        - bin_size must be greater than zero (step_size must be checked at construction)
        - bin_size must be greater or equal than step_size (to avoid gaps)
        - bin_size must be less than or equal to roi width and height (to fit in the roi)
        Returns:
            validity (bool), message (str)
        """
        if self.bin_size < 1:
            return False, "bin_size must be greater than zero"
        if self.bin_size < self.step_size:
            return False, "bin_size must be greater or equal than step_size"
        if self.bin_size > self.roi.width or self.bin_size > self.roi.height:
            return False, "step_size must be less than or equal to roi width and height"

        return True, ""
