# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from pathlib import Path
from typing import ClassVar, Type


class LogColumn(Enum):
    TIMESTAMP = auto()
    IMAGE_TYPE_IMAGE_COUNTER = auto()
    PROJECTION_NUMBER = auto()
    PROJECTION_ANGLE = auto()
    COUNTS_BEFORE = auto()
    COUNTS_AFTER = auto()
    TIME_OF_FLIGHT = auto()
    SPECTRUM_COUNTS = auto()


LogDataType = dict[LogColumn, list[float | int]]


class NoParserFound(RuntimeError):
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


class InstrumentLog:
    """Multiformat instrument log reader

    New parsers can be implemented by subclassing InstrumentLogParser
    """
    parsers: ClassVar[list[Type[InstrumentLogParser]]] = []

    parser: Type[InstrumentLogParser]
    data: LogDataType

    def __init__(self, lines: list[str], source_file: Path):
        self.lines = lines
        self.source_file = source_file

        self._clean_lines()

        self._find_parser()
        self.parse()

    def _clean_lines(self) -> None:
        """Remove blank lines"""
        self.lines = [line for line in self.lines if line.strip() != ""]

    def _find_parser(self) -> None:
        for parser in self.parsers:
            if parser.match(self.lines, self.source_file.name):
                self.parser = parser
                return
        raise NoParserFound

    def parse(self) -> None:
        self.data = self.parser(self.lines).parse()

    @classmethod
    def register_parser(cls, parser: Type[InstrumentLogParser]) -> None:
        cls.parsers.append(parser)

    def get_column(self, key: LogColumn) -> list[float]:
        return self.data[key]
