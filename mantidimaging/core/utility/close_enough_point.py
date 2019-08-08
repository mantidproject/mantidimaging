from typing import TypeVar, List, Union

T = TypeVar("T")


class CloseEnoughPoint:
    """
    This point is close enough to the real positions, as it rounds
    up to integers so that actual pixel values can be used
    """
    __slots__ = ("y", "x")
    y: int
    x: int

    def __init__(self, points: List[Union[int, float]]):
        self.y = int(points[1])
        self.x = int(points[0])
