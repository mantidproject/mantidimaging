from enum import Enum, auto
from typing import List, Dict

import numpy

from mantidimaging.core.utility.data_containers import ProjectionAngles, Counts


class IMATLogColumn(Enum):
    TIMESTAMP = auto()
    # currently these 2 are the same column because
    # the log file formatting is inconsistent
    IMAGE_TYPE_IMAGE_COUNTER = auto()
    COUNTS_BEFORE = auto()
    COUNTS_AFTER = auto()


class IMATLogFile:
    def __init__(self, data: List[List[str]]):
        self._data: Dict[IMATLogColumn, List] = {
            IMATLogColumn.TIMESTAMP: [],
            IMATLogColumn.IMAGE_TYPE_IMAGE_COUNTER: [],
            IMATLogColumn.COUNTS_BEFORE: [],
            IMATLogColumn.COUNTS_AFTER: []
        }
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
            if "angle:" not in angle_str:
                raise ValueError("Projection angles loaded from logfile do not have the correct formatting!")
            angles[i] = float(angle_str[angle_str.rfind(": ") + 1:])

        return ProjectionAngles(numpy.deg2rad(angles))

    def counts(self) -> Counts:
        counts = numpy.zeros(len(self._data[IMATLogColumn.COUNTS_BEFORE]))
        for i, [before,
                after] in enumerate(zip(self._data[IMATLogColumn.COUNTS_BEFORE],
                                        self._data[IMATLogColumn.COUNTS_AFTER])):

            # clips the string before the count number
            before = before[before.rfind(":") + 1:]
            after = after[after.rfind(":") + 1:]
            counts[i] = float(after) - float(before)

        return Counts(counts)
