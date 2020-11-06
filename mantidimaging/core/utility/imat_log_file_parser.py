from enum import Enum, auto
from itertools import zip_longest
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

    def projection_numbers(self):
        proj_nums = numpy.zeros(len(self._data[IMATLogColumn.IMAGE_TYPE_IMAGE_COUNTER]), dtype=numpy.uint32)
        for i, angle_str in enumerate(self._data[IMATLogColumn.IMAGE_TYPE_IMAGE_COUNTER]):
            if "angle:" not in angle_str:
                raise ValueError("Projection angles loaded from logfile do not have the correct formatting!")
            proj_nums[i] = int(angle_str[angle_str.find(": ") + 1:angle_str.find("a")])

        return proj_nums

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

    def raise_if_angle_missing(self, image_filenames):
        proj_numbers = self.projection_numbers()
        image_numbers = [ifile[ifile.rfind("_") + 1:] for ifile in image_filenames]

        if len(proj_numbers) < len(image_numbers):
            msg = "Missing projection from log. "
        elif len(proj_numbers) > len(image_numbers):
            msg = "Missing image file from sample data. "
        else:
            msg = ""
        msg += f"Found {len(proj_numbers)} angles, but {len(image_numbers)} images"

        for projection_num, image_num in zip_longest(proj_numbers, image_numbers):
            # is None happens if exactly the last projection/angle is missing
            if projection_num is None or image_num is None or str(projection_num) not in image_num:
                raise RuntimeError(f"{msg}\n\nMismatching angle for projection {projection_num} "
                                   f"was going to be used for image file {image_num}")
