from dataclasses import dataclass

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
