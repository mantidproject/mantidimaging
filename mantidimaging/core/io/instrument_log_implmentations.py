# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import csv
import locale
from datetime import datetime
from pathlib import Path

from mantidimaging.core.io.instrument_log import (InstrumentLogParser, InstrumentShutterCountParser, LogColumn,
                                                  ShutterCountColumn, LogDataType, ShutterCountType)
from mantidimaging.core.utility.imat_log_file_parser import IMATLogFile, IMATLogColumn


class LegacySpectraLogParser(InstrumentLogParser):
    """
    Parser for spectra files without a header

    Tab separated columns of Time of flight [s], Counts

    """
    delimiter = '\t'

    @classmethod
    def match(cls, lines: list[str], filename: str) -> bool:
        if not filename.lower().endswith("spectra.txt"):
            return False
        for line in lines[:2]:
            if not len(line.split(cls.delimiter)) == 2:
                return False
        return True

    def parse(self) -> LogDataType:
        data: LogDataType = {LogColumn.TIME_OF_FLIGHT: [], LogColumn.SPECTRUM_COUNTS: []}
        for row in csv.reader(self.cleaned_lines(), delimiter=self.delimiter):
            data[LogColumn.TIME_OF_FLIGHT].append(float(row[0]))
            data[LogColumn.SPECTRUM_COUNTS].append(int(row[1]))
        return data


class LegacyShutterCountLogParser(InstrumentShutterCountParser):
    """
    Parser for shutter count files without a header searching for files ending in "ShutterCount.txt"
    Tab separated columns of Pulse number, Shutter count
    """
    delimiter = '\t'

    @classmethod
    def match(cls, lines: list[str], filename: str) -> bool:
        if not filename.lower().endswith("shuttercount.txt"):
            return False
        for line in lines[:2]:
            parts = line.split(cls.delimiter)
            if len(parts) != 2:
                return False
        return True

    def parse(self) -> ShutterCountType:
        data: ShutterCountType = {ShutterCountColumn.PULSE: [], ShutterCountColumn.SHUTTER_COUNT: []}
        for row in csv.reader(self.cleaned_lines(), delimiter=self.delimiter):
            data[ShutterCountColumn.PULSE].append(int(row[0]))
            data[ShutterCountColumn.SHUTTER_COUNT].append(int(row[1]))
        return data


class LegacyIMATLogFile(InstrumentLogParser):
    """Wrap existing IMATLogFile class"""

    @classmethod
    def match(cls, lines: list[str], filename: str) -> bool:
        if filename.lower()[-4:] not in [".txt", ".csv"]:
            return False

        has_header = False
        for line in lines:
            if not has_header and cls._has_imat_header(line):
                has_header = True
            elif has_header and cls._has_imat_data_line(line):
                return True

        return False

    def parse(self) -> LogDataType:
        imat_log_file = IMATLogFile(self.lines, Path(""))
        data: LogDataType = {}
        data[LogColumn.TIMESTAMP] = imat_log_file._data[IMATLogColumn.TIMESTAMP]
        data[LogColumn.PROJECTION_NUMBER] = imat_log_file._data[IMATLogColumn.PROJECTION_NUMBER]
        data[LogColumn.PROJECTION_ANGLE] = imat_log_file._data[IMATLogColumn.PROJECTION_ANGLE]
        data[LogColumn.COUNTS_BEFORE] = imat_log_file._data[IMATLogColumn.COUNTS_BEFORE]
        data[LogColumn.COUNTS_AFTER] = imat_log_file._data[IMATLogColumn.COUNTS_AFTER]
        return data

    @staticmethod
    def read_imat_date(time_stamp: str) -> datetime:
        lc = locale.setlocale(locale.LC_TIME)
        try:
            locale.setlocale(locale.LC_TIME, "C")
            return datetime.strptime(time_stamp, "%c")
        finally:
            locale.setlocale(locale.LC_TIME, lc)

    @staticmethod
    def _has_imat_header(line: str) -> bool:
        HEADERS = [
            "TIME STAMP,IMAGE TYPE,IMAGE COUNTER,COUNTS BM3 before image,COUNTS BM3 after image",
            "TIME STAMP  IMAGE TYPE   IMAGE COUNTER   COUNTS BM3 before image   COUNTS BM3 after image",
        ]
        return line.strip() in HEADERS

    @classmethod
    def _has_imat_data_line(cls, line: str) -> bool:
        try:
            _ = cls.read_imat_date(line[:24])
        except ValueError:
            return False

        if not ("Projection" in line or "Radiography" in line):
            return False

        return True
