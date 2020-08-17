from enum import Enum, auto
from typing import List, Dict

import numpy

from mantidimaging.core.utility.data_containers import ProjectionAngles


class IMATLogColumn(Enum):
    TIMESTAMP = auto()
    # currently these 2 are the same column because
    # the log file formatting is inconsistent
    IMAGE_TYPE_IMAGE_COUNTER = auto()
    COUNTS_BEFORE = auto()
    COUNTS_AFTER = auto()


class IMATLogFile:
    _data: Dict[IMATLogColumn, List] = {
        IMATLogColumn.TIMESTAMP: [],
        IMATLogColumn.IMAGE_TYPE_IMAGE_COUNTER: [],
        IMATLogColumn.COUNTS_BEFORE: [],
        IMATLogColumn.COUNTS_AFTER: []
    }

    def __init__(self, data: List[List[str]]):
        # ignores the headers (index 0) as they're not the same as the data anyway
        # and index 1 is an empty line
        for line in data[2:]:
            self._data[IMATLogColumn.TIMESTAMP].append(line[0])
            self._data[IMATLogColumn.IMAGE_TYPE_IMAGE_COUNTER].append(line[1])
            self._data[IMATLogColumn.COUNTS_BEFORE].append(line[2])
            self._data[IMATLogColumn.COUNTS_AFTER].append(line[3])

    def projection_angles(self) -> ProjectionAngles:
        angles = numpy.zeros(len(self._data[IMATLogColumn.IMAGE_TYPE_IMAGE_COUNTER]))
        for i, angle_str in enumerate(self._data[IMATLogColumn.IMAGE_TYPE_IMAGE_COUNTER]):
            assert "angle:" in angle_str
            angles[i] = float(angle_str[angle_str.rfind(": ") + 1:])

        return ProjectionAngles(numpy.deg2rad(angles))
