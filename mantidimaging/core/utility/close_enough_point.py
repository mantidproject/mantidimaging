# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class CloseEnoughPoint:
    """
    Rounds down point values to the closest integers so it can be used as a pixel coordinate
    """
    __slots__ = ("y", "x")
    y: int
    x: int

    def __init__(self, points: Union[Sequence[int], Sequence[float]]):
        self.y = int(points[1])
        self.x = int(points[0])

    def __str__(self):
        return f"({self.x}, {self.y})"
