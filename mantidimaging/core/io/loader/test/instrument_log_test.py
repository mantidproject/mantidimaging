# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from pathlib import Path

from numpy.testing import assert_allclose

from .instrument_log_data import (IMAT_2023_SPECTRA_LOG, INVALID_FILE, IMAT_2019_TOMO_LOG, CSV_SAMPLE_LOG,
                                  CSV_SAMPLE_LOG_EXTRA_COLUMNS, CSV_MINIMAL_COLUMNS)
from mantidimaging.core.io.instrument_log import LogColumn, InstrumentLog, NoParserFound


class FilenamePatternTest(unittest.TestCase):

    def check_parse_data(self, log_data, key, expected_values):
        filename, data = log_data
        log = InstrumentLog(data.split("\n"), Path(filename))
        assert_allclose(log.get_column(key), expected_values)

    def test_WHEN_read_spectra_file_THEN_expected_values_read(self):
        self.check_parse_data(IMAT_2023_SPECTRA_LOG, LogColumn.TIME_OF_FLIGHT, [0.012, 0.012041, 0.0120819, 0.0121229])
        self.check_parse_data(IMAT_2023_SPECTRA_LOG, LogColumn.SPECTRUM_COUNTS, [334937, 331913, 331737, 331161])

    def test_WHEN_read_imat_2019_file_THEN_expected_values_read(self):
        self.check_parse_data(IMAT_2019_TOMO_LOG, LogColumn.PROJECTION_NUMBER, [0, 1, 2, 3])
        self.check_parse_data(IMAT_2019_TOMO_LOG, LogColumn.PROJECTION_ANGLE, [0, 0.3152, 0.6304, 0.9456])

    def test_WHEN_invalid_file_THEN_exception(self):
        filename, data = INVALID_FILE
        self.assertRaises(NoParserFound, InstrumentLog, data, Path(filename))

    def test_WHEN_read_strict_csv_file_THEN_expected_values_read(self):
        self.check_parse_data(CSV_SAMPLE_LOG, LogColumn.PROJECTION_NUMBER, [0, 1, 2, 3])
        self.check_parse_data(CSV_SAMPLE_LOG, LogColumn.PROJECTION_ANGLE, [0, 0.3152, 0.6304, 0.9456])

    def test_WHEN_read_csv_with_extra_columns_THEN_expected_values_read(self):
        self.check_parse_data(CSV_SAMPLE_LOG_EXTRA_COLUMNS, LogColumn.PROJECTION_NUMBER, [0, 1, 2, 3])
        self.check_parse_data(CSV_SAMPLE_LOG_EXTRA_COLUMNS, LogColumn.PIXEL_SIZE, [29.0, 29.0, 29.0, 29.0])

    def test_WHEN_read_csv_with_extra_columns_THEN_unexpected_cols_skipped(self):
        self.assertRaises(
            KeyError, lambda: InstrumentLog(CSV_SAMPLE_LOG_EXTRA_COLUMNS[1].split("\n"),
                                            Path(CSV_SAMPLE_LOG_EXTRA_COLUMNS[0])).get_column("TEMPERATURE"))

    def test_WHEN_read_csv_with_minimal_columns_THEN_expected_values_read(self):
        self.check_parse_data(CSV_MINIMAL_COLUMNS, LogColumn.PROJECTION_NUMBER, [0, 1, 2, 3])
