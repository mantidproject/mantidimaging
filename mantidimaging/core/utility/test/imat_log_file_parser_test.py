# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
import pytest

from mantidimaging.core.utility.imat_log_file_parser import CSVLogParser, IMATLogFile, TextLogParser, \
    _get_projection_number


@pytest.mark.parametrize('test_input', [[
    TextLogParser.EXPECTED_HEADER_FOR_IMAT_TEXT_LOG_FILE, "ignored line",
    "timestamp   Projection:  0  angle: 0.1   counts before: 12345   counts_after: 45678"
],
                                        [
                                            CSVLogParser.EXPECTED_HEADER_FOR_IMAT_CSV_LOG_FILE,
                                            "timestamp,Projection,0,angle:0.1,counts before: 12345,counts_after: 45678"
                                        ]])
def test_parsing_log_file(test_input):
    logfile = IMATLogFile(test_input, "/tmp/fake")
    assert len(logfile.projection_angles().value) == 1
    assert logfile.projection_angles().value[0] == np.deg2rad(0.1), f"Got: {logfile.projection_angles().value[0]}"
    assert logfile.counts().value[0] == (45678 - 12345)


TXT_LOG_FILE = [
    TextLogParser.EXPECTED_HEADER_FOR_IMAT_TEXT_LOG_FILE,
    "ignored line",
    "timestamp   Projection:  0  angle: 0.0   counts before: 12345   counts_after: 45678",
    "timestamp   Projection:  1  angle: 0.1   counts before: 45678   counts_after: 84678",
    "timestamp   Projection:  2  angle: 0.2   counts before: 84678   counts_after: 124333",
]
CSV_LOG_FILE = [
    CSVLogParser.EXPECTED_HEADER_FOR_IMAT_CSV_LOG_FILE,
    "timestamp,Projection,0,angle:0.0,counts before: 12345,counts_after: 45678",
    "timestamp,Projection,1,angle:0.1,counts before: 45678,counts_after: 84678",
    "timestamp,Projection,2,angle:0.2,counts before: 84678,counts_after: 124333",
]


@pytest.mark.parametrize('test_input', [TXT_LOG_FILE, CSV_LOG_FILE])
def test_counts(test_input):
    logfile = IMATLogFile(test_input, "/tmp/fake")
    assert len(logfile.counts().value) == 3
    assert logfile.counts().value[0] == 45678 - 12345
    assert logfile.counts().value[1] == 84678 - 45678
    assert logfile.counts().value[2] == 124333 - 84678


def test_counts_compare():
    logfile = IMATLogFile(TXT_LOG_FILE, "/tmp/fake")
    logfile_from_csv = IMATLogFile(CSV_LOG_FILE, "/tmp/fake")

    assert len(logfile.counts().value) == len(logfile_from_csv.counts().value)
    assert logfile.counts().value[0] == logfile_from_csv.counts().value[0]
    assert logfile.counts().value[1] == logfile_from_csv.counts().value[1]
    assert logfile.counts().value[2] == logfile_from_csv.counts().value[2]


def assert_raises(exc_type, callable, *args, **kwargs):
    try:
        callable(*args, **kwargs)
        raise AssertionError("Did not raise")
    except exc_type:
        return
    except Exception:
        raise AssertionError("Did not raise expected exception.")


@pytest.mark.parametrize('test_input', [TXT_LOG_FILE, CSV_LOG_FILE])
def test_find_missing_projection_number(test_input):
    logfile = IMATLogFile(test_input, "/tmp/fake")
    assert len(logfile.projection_numbers()) == 3
    # nothing missing
    logfile.raise_if_angle_missing(["file_000.tif", "file_001.tif", "file_002.tif"])
    # image file missing
    assert_raises(RuntimeError, logfile.raise_if_angle_missing, ["file_000.tif", "file_002.tif"])
    # image file missing
    assert_raises(RuntimeError, logfile.raise_if_angle_missing, ["file_000.tif", "file_001.tif"])
    assert_raises(RuntimeError, logfile.raise_if_angle_missing,
                  ["file_000.tif", "file_001.tif", "file_002.tif", "file_003.tif"])


def test_raise_if_angles_missing_returns_none_if_no_filename_list():
    logfile = IMATLogFile(TXT_LOG_FILE, "/tmp/fake")
    assert logfile.raise_if_angle_missing(None) is None


@pytest.mark.parametrize('test_input', [TXT_LOG_FILE, CSV_LOG_FILE])
def test_source_file(test_input):
    logfile = IMATLogFile(test_input, "/tmp/fake")
    assert logfile.source_file == "/tmp/fake"


def test_get_projection_number():
    assert _get_projection_number("Projection:  99  angle: 31.2048") == 99
    assert _get_projection_number("Radiography:  19") == 19


def test_ignore_spaces_at_end_of_log_file_header():
    test_log_file = TXT_LOG_FILE[:]
    test_log_file[0].replace("\n", "         \n")
    logfile = IMATLogFile(test_log_file, "/tmp/fake")
    assert len(logfile.projection_numbers()) == 3
