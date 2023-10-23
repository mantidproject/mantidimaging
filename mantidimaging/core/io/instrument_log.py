# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from pathlib import Path
from typing import ClassVar, Type

import numpy as np

from mantidimaging.core.utility.data_containers import ProjectionAngles, Counts


class LogColumn(Enum):
    TIMESTAMP = auto()
    IMAGE_TYPE_IMAGE_COUNTER = auto()
    PROJECTION_NUMBER = auto()
    PROJECTION_ANGLE = auto()
    COUNTS_BEFORE = auto()
    COUNTS_AFTER = auto()
    TIME_OF_FLIGHT = auto()  # in seconds
    SPECTRUM_COUNTS = auto()


LogDataType = dict[LogColumn, list[float | int]]


class NoParserFound(RuntimeError):
    pass


class InvalidLog(RuntimeError):
    pass


class InstrumentLogParser(ABC):
    """
    Base class for parsers
    """

    def __init__(self, lines: list[str]):
        self.lines = lines

    def __init_subclass__(subcls) -> None:
        """Automatically register subclasses"""
        InstrumentLog.register_parser(subcls)

    @classmethod
    @abstractmethod
    def match(cls, lines: list[str], filename: str) -> bool:
        """Check if the name and content of the file is likely to be readable by this parser."""
        ...

    @abstractmethod
    def parse(self) -> LogDataType:
        """Parse the log file"""
        ...

    def cleaned_lines(self) -> list[str]:
        return [line for line in self.lines if line.strip() != ""]


class InstrumentLog:
    """Multiformat instrument log reader

    New parsers can be implemented by subclassing InstrumentLogParser
    """
    parsers: ClassVar[list[Type[InstrumentLogParser]]] = []

    parser: Type[InstrumentLogParser]
    data: LogDataType
    length: int

    def __init__(self, lines: list[str], source_file: Path):
        self.lines = lines
        self.source_file = source_file

        self._find_parser()
        self.parse()

    def _find_parser(self) -> None:
        for parser in self.parsers:
            if parser.match(self.lines, self.source_file.name):
                self.parser = parser
                return
        raise NoParserFound

    def parse(self) -> None:
        self.data = self.parser(self.lines).parse()

        lengths = [len(val) for val in self.data.values()]
        if len(set(lengths)) != 1:
            raise InvalidLog(f"Mismatch in column lengths: {lengths}")
        self.length = lengths[0]

    @classmethod
    def register_parser(cls, parser: Type[InstrumentLogParser]) -> None:
        cls.parsers.append(parser)

    def get_column(self, key: LogColumn) -> list[float]:
        return self.data[key]

    def projection_numbers(self) -> np.array:
        return np.array(self.get_column(LogColumn.PROJECTION_NUMBER), dtype=np.uint32)

    def has_projection_angles(self) -> bool:
        return LogColumn.PROJECTION_ANGLE in self.data

    def projection_angles(self) -> ProjectionAngles:
        angles = np.array(self.get_column(LogColumn.PROJECTION_ANGLE), dtype=np.float64)
        return ProjectionAngles(np.deg2rad(angles))

    def raise_if_angle_missing(self, image_filenames: list[str]) -> None:
        image_numbers = [ifile[ifile.rfind("_") + 1:] for ifile in image_filenames]

        if self.length != len(image_numbers):
            RuntimeError(f"Log size mismatch. Found {self.length} log entries,"
                         f"but {len(image_numbers)} images")

        if LogColumn.PROJECTION_NUMBER in self.data:
            for projection_num, image_num in zip(self.projection_numbers(), image_numbers, strict=True):
                if str(projection_num) not in image_num:
                    raise RuntimeError(f"Mismatching angle for projection {projection_num} "
                                       f"was going to be used for image file {image_num}")

    def counts(self) -> Counts:
        if not (LogColumn.COUNTS_BEFORE in self.data and LogColumn.COUNTS_AFTER in self.data):
            raise ValueError("Log does not have counts")

        counts_before = np.array(self.get_column(LogColumn.COUNTS_BEFORE))
        counts_after = np.array(self.get_column(LogColumn.COUNTS_AFTER))

        return Counts(counts_after - counts_before)
