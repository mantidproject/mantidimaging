from dataclasses import dataclass

from mantidimaging.external.pyqtgraph.imageview import SensiblePoint


@dataclass
class SensibleROI:
    __slots__ = ("left", "top", "right", "bottom")
    left: int
    top: int
    right: int
    bottom: int

    @staticmethod
    def from_points(position: SensiblePoint, size: SensiblePoint) -> 'SensibleROI':
        return SensibleROI(position.x, position.y, position.x + size.x, position.y + size.y)
