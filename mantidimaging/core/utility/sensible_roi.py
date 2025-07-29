# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
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

    def __eq__(self, other) -> bool:
        if not isinstance(other, SensibleROI):
            return NotImplemented
        return (self.left, self.top, self.right, self.bottom) == (other.left, other.top, other.right, other.bottom)

    def __hash__(self) -> int:
        return hash((self.left, self.top, self.right, self.bottom))

    @staticmethod
    def from_points(position: CloseEnoughPoint, size: CloseEnoughPoint) -> SensibleROI:
        return SensibleROI(position.x, position.y, position.x + size.x, position.y + size.y)

    @staticmethod
    def from_list(roi: list[int] | list[float]) -> SensibleROI:
        return SensibleROI(int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3]))

    def __iter__(self) -> Iterator[int]:
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
