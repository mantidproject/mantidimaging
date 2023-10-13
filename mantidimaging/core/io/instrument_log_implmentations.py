# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import csv

from mantidimaging.core.io.instrument_log import (InstrumentLogParser, LogColumn, LogDataType)


class LegacySpectraLogParser(InstrumentLogParser):
    """
    Parser for spectra files without a header

    Tab separated columns of Time of flight, Counts

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
