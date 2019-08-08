from typing import TypeVar, Generic, List

T = TypeVar("T")


class SensiblePoint(Generic[T]):
    __slots__ = ("y", "x")
    y: T
    x: T

    def __init__(self, points: List[T]):
        self.y = points[1]
        self.x = points[0]
