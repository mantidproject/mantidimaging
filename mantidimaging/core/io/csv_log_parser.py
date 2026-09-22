# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from __future__ import annotations

import csv
from collections.abc import Callable, Sequence
from logging import getLogger
from pathlib import Path

from mantidimaging.core.io.instrument_log import InstrumentLogParser, LogColumn, LogDataType

LOG = getLogger(__name__)


class CSVLogFileParser(InstrumentLogParser):
    """
    Parser for instrument logs written as a strict CSV file with a header row.

    Requires a .csv suffix and an IMAGE COUNTER header. All other columns are optional.
    Known optional headers are parsed when present.
    """
    REQUIRED_HEADERS: frozenset[str] = frozenset({"IMAGE COUNTER"})
    COLUMN_DEFINITIONS: dict[str, tuple[LogColumn, Callable[[str], str | float | int]]] = {
        "TIME STAMP": (LogColumn.TIMESTAMP, str),
        "IMAGE TYPE": (LogColumn.IMAGE_TYPE_IMAGE_COUNTER, str),
        "IMAGE COUNTER": (LogColumn.PROJECTION_NUMBER, int),
        "PROJECTION ANGLE DEG": (LogColumn.PROJECTION_ANGLE, float),
        "PIXEL SIZE": (LogColumn.PIXEL_SIZE, float),
        "COUNTS BEFORE": (LogColumn.COUNTS_BEFORE, int),
        "COUNTS AFTER": (LogColumn.COUNTS_AFTER, int),
    }

    @classmethod
    def match(cls, lines: list[str], filename: str) -> bool:
        """
        Override InstrumentLogParser.match to return if lines
        and filename match expeted format for a strict CSV log file.
        Matches if extra whitespace around headers exists.
        """
        if Path(filename).suffix.lower() != ".csv":
            return False
        if not lines:
            return False
        headers = {header.strip() for header in lines[0].split(",")}
        return cls.REQUIRED_HEADERS.issubset(headers)

    def parse(self) -> LogDataType:
        """
        Parse CSV log file to dictionary map, clearing headers of whitespace and
        checking for optional and unrecognised headers
        """
        lines = [line for line in self.lines if line != ""]
        reader = csv.DictReader(lines)
        fieldnames = reader.fieldnames
        rows = [{header.strip(): value for header, value in row.items()} for row in list(reader)]

        if fieldnames is None:
            raise ValueError("CSV log file is missing header row")
        fieldnames = [header.strip() for header in fieldnames]

        self._log_unrecognised_headers(fieldnames)

        return self._parse_columns(fieldnames, rows)

    @classmethod
    def _log_unrecognised_headers(cls, fieldnames: Sequence[str]) -> None:
        """
        Log unrecognised headers to ensure it is clear what data is and isn't being parsed
        """
        unrecognised = set(fieldnames) - cls.COLUMN_DEFINITIONS.keys()
        if unrecognised:
            LOG.warning(f"Ignoring unrecognised CSV headers: {unrecognised}")

    @classmethod
    def _parse_columns(cls, fieldnames: Sequence[str], rows: list[dict[str, str]]) -> LogDataType:
        """
        Parse one known CSV headers and convert to mapped types

        :return: supported log data represented as dict mapping LogColumn
        """
        data: LogDataType = {}

        for header, (column, converter) in cls.COLUMN_DEFINITIONS.items():
            if header not in fieldnames:
                continue
            column_values = [converter(row[header]) for row in rows]
            data[column] = column_values

        return data
