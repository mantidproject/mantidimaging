from dataclasses import dataclass
from typing import Union, List

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint


@dataclass
class SensibleROI:
    __slots__ = ("left", "top", "right", "bottom")
    left: int
    top: int
    right: int
    bottom: int

    @staticmethod
    def from_points(position: CloseEnoughPoint, size: CloseEnoughPoint) -> 'SensibleROI':
        return SensibleROI(position.x, position.y, position.x + size.x, position.y + size.y)

    @staticmethod
    def from_list(roi: List[Union[int, float]]):
        return SensibleROI(roi[0], roi[1], roi[2], roi[3])

    def __iter__(self):
        """
        Allows unpacking the ROI with `*roi`
        :return: Iterable of all ROI parts
        """
        return iter((self.left, self.top, self.right, self.bottom))

    def __str__(self):
        return f"Left: {self.left}, Top: {self.top}, Right: {self.right}, Bottom: {self.bottom}"

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top
