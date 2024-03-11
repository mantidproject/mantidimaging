# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import csv
import re
from enum import Enum, auto
from itertools import zip_longest
from logging import getLogger
from typing import Optional, TYPE_CHECKING

import numpy

from mantidimaging.core.utility.data_containers import Counts, ProjectionAngles

if TYPE_CHECKING:
    from pathlib import Path

LOG = getLogger(__name__)


def _get_projection_number(s: str) -> int:
    return int(re.sub(r"\D", "", s.split(":")[1]))


def _get_angle(s: str) -> str:
    return s[s.rfind(":") + 1:].strip()


class IMATLogColumn(Enum):
    TIMESTAMP = auto()
    # currently these 2 are the same column because
    # the log file formatting is inconsistent
    IMAGE_TYPE_IMAGE_COUNTER = auto()
    PROJECTION_NUMBER = auto()
    PROJECTION_ANGLE = auto()
    COUNTS_BEFORE = auto()
    COUNTS_AFTER = auto()


class TextLogParser:
    EXPECTED_HEADER_FOR_IMAT_TEXT_LOG_FILE = \
            ' TIME STAMP  IMAGE TYPE   IMAGE COUNTER   COUNTS BM3 before image   COUNTS BM3 after image\n'

    def __init__(self, data: list[str]) -> None:
        self.data = [line.strip().split("   ") for line in data]

    def parse(self) -> dict[IMATLogColumn, list]:
        parsed_log: dict[IMATLogColumn, list] = {
            IMATLogColumn.TIMESTAMP: [],
            IMATLogColumn.PROJECTION_NUMBER: [],
            IMATLogColumn.PROJECTION_ANGLE: [],
            IMATLogColumn.COUNTS_BEFORE: [],
            IMATLogColumn.COUNTS_AFTER: []
        }
        # ignores the headers (index 0) as they're not the same as the data anyway
        # and index 1 is an empty line
        try:
            for line in self.data[2:]:
                parsed_log[IMATLogColumn.TIMESTAMP].append(line[0])
                parsed_log[IMATLogColumn.PROJECTION_NUMBER].append(_get_projection_number(line[1]))
                parsed_log[IMATLogColumn.PROJECTION_ANGLE].append(float(_get_angle(line[1])))
                parsed_log[IMATLogColumn.COUNTS_BEFORE].append(int(_get_angle(line[2])))
                parsed_log[IMATLogColumn.COUNTS_AFTER].append(int(_get_angle(line[3])))
            return parsed_log
        except ValueError as value_error:
            raise ValueError(
                f"Unable to parse value from log file to correct type for row: {line} {value_error}") from value_error
        except IndexError as index_error:
            raise IndexError(
                f"Unable to parse value from log file to correct type for row: {line} {index_error}") from index_error

    @staticmethod
    def try_insert_header(file_contents: list[str]) -> list[str]:
        """
        Attempt to normalise data where no header is present by inserting one.

        @param file_contents: The file contents to be reformatted
        @return: The reformatted file contents
        """
        first_row = file_contents[0].rstrip()
        if TextLogParser.EXPECTED_HEADER_FOR_IMAT_TEXT_LOG_FILE != first_row + "\n":
            if len(first_row.split("   ")) < 4:
                LOG.warning(f"\nInvalid log file header:\n{file_contents[0]}" +
                            f"Replacing with:\n{TextLogParser.EXPECTED_HEADER_FOR_IMAT_TEXT_LOG_FILE}")
                file_contents.remove(file_contents[0])
            file_contents.insert(0, TextLogParser.EXPECTED_HEADER_FOR_IMAT_TEXT_LOG_FILE)
            file_contents.insert(1, " ")
        return file_contents

    @staticmethod
    def try_remove_invalid_lines(file_contents: list[str]) -> list[str]:
        """
        Attempt to normalise data where invalid lines are the incorrect number of columns are present.

        @param file_contents: The file contents to be reformatted
        @return: The reformatted file contents
        """
        cleaned = file_contents[:2]  # parser expect second like to be blank
        cleaned += [row for row in file_contents[2:] if len(row.rstrip().split("   ")) >= 4]
        return cleaned


class CSVLogParser:
    EXPECTED_HEADER_FOR_IMAT_CSV_LOG_FILE = \
        "TIME STAMP,IMAGE TYPE,IMAGE COUNTER,COUNTS BM3 before image,COUNTS BM3 after image\n"

    def __init__(self, data: list[str]) -> None:
        self.data = data

    def parse(self) -> dict[IMATLogColumn, list]:
        parsed_log: dict[IMATLogColumn, list] = {
            IMATLogColumn.TIMESTAMP: [],
            IMATLogColumn.PROJECTION_NUMBER: [],
            IMATLogColumn.PROJECTION_ANGLE: [],
            IMATLogColumn.COUNTS_BEFORE: [],
            IMATLogColumn.COUNTS_AFTER: []
        }

        reader = csv.reader(self.data)

        # skip headings
        next(reader)
        try:
            for row in reader:

                parsed_log[IMATLogColumn.TIMESTAMP].append(row[0])
                parsed_log[IMATLogColumn.PROJECTION_NUMBER].append(int(row[2]))
                angle_raw = row[3]
                parsed_log[IMATLogColumn.PROJECTION_ANGLE].append(float(_get_angle(angle_raw)))

                counts_before_raw = row[4]
                parsed_log[IMATLogColumn.COUNTS_BEFORE].append(int(_get_angle(counts_before_raw)))

                counts_after_raw = row[5]
                parsed_log[IMATLogColumn.COUNTS_AFTER].append(int(_get_angle(counts_after_raw)))
            return parsed_log
        except ValueError as value_error:
            raise ValueError(
                f"Unable to parse value from log file to correct type for row: {row} {value_error}") from value_error

    @staticmethod
    def try_insert_header(file_contents: list[str]) -> list[str]:
        """
        Attempt to normalise data where no header is present by inserting one.

        @param file_contents: The file contents to be reformatted
        @return: The reformatted file contents
        """
        if CSVLogParser.EXPECTED_HEADER_FOR_IMAT_CSV_LOG_FILE != file_contents[0]:
            file_contents.insert(0, CSVLogParser.EXPECTED_HEADER_FOR_IMAT_CSV_LOG_FILE)

        return file_contents

    @staticmethod
    def try_remove_invalid_lines(file_contents: list[str]) -> list[str]:
        """
        Attempt to normalise data where invalid lines are the incorrect number of columns are present.

        @param file_contents: The file contents to be reformatted
        @return: The reformatted file contents
        """
        cleaned = [row for row in file_contents if len(row.split(",")) >= 5]
        return cleaned


class IMATLogFile:

    def __init__(self, data: list[str], source_file: Path):
        self._source_file = source_file

        self.parser = self.find_parser(data)
        self._data = self.parser.parse()

    @staticmethod
    def find_parser(data: list[str]):
        """
        Try and determine the format of the log file by checking the first row. for the type of seperator used and then
        attempting to normalise the data if needed before selecting the appropriate parser.
        """

        if IMATLogFile.get_seperator(data[0]):
            data = TextLogParser.try_insert_header(data)
            data = TextLogParser.try_remove_invalid_lines(data)
            return TextLogParser(data)
        elif not IMATLogFile.get_seperator(data[0]):
            data = CSVLogParser.try_insert_header(data)
            data = CSVLogParser.try_remove_invalid_lines(data)
            return CSVLogParser(data)

    @staticmethod
    def get_seperator(first_row: str) -> bool:
        """
        Try and determine the seperator used in the log file.
        If neither a tab or comma is found, then return a RuntimeError
        as the format is not recognised.

        @param data: The file contents to be checked
        @return: The seperator used in the file
        Exception: RuntimeError if the format is not recognised
        """
        if "   " in first_row:
            return True
        elif "," in first_row:
            return False
        else:
            raise RuntimeError("The format of the log file is not recognised.")

    @property
    def source_file(self) -> Path:
        return self._source_file

    def projection_numbers(self):
        proj_nums = numpy.zeros(len(self._data[IMATLogColumn.PROJECTION_NUMBER]), dtype=numpy.uint32)
        proj_nums[:] = self._data[IMATLogColumn.PROJECTION_NUMBER]
        return proj_nums

    def projection_angles(self) -> ProjectionAngles:
        angles = numpy.zeros(len(self._data[IMATLogColumn.PROJECTION_ANGLE]))
        angles[:] = self._data[IMATLogColumn.PROJECTION_ANGLE]
        return ProjectionAngles(numpy.deg2rad(angles))

    def counts(self) -> Counts:
        counts = numpy.zeros(len(self._data[IMATLogColumn.COUNTS_BEFORE]))
        for i, [before, after] in enumerate(
                zip(self._data[IMATLogColumn.COUNTS_BEFORE], self._data[IMATLogColumn.COUNTS_AFTER], strict=True)):
            # clips the string before the count number
            counts[i] = float(after) - float(before)

        return Counts(counts)

    def raise_if_angle_missing(self, image_filenames: Optional[list[str]]) -> None:
        if image_filenames is None:
            return

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
