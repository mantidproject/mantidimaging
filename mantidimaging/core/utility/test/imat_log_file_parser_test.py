# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import numpy as np

from mantidimaging.core.utility.imat_log_file_parser import IMATLogFile


def test_parsing_log_file():
    test_input = [["ignored line"], ["ignored line"],
                  ["timestamp", "Projection:  0  angle: 0.1", "counts before: 12345", "counts_after: 45678"]]
    logfile = IMATLogFile(test_input)
    assert len(logfile.projection_angles().value) == 1
    assert logfile.projection_angles().value[0] == np.deg2rad(0.1), f"Got: {logfile.projection_angles().value[0]}"
    assert logfile.counts().value[0] == (45678 - 12345)


def test_counts():
    test_input = [
        ["ignored line"],
        ["ignored line"],
        ["timestamp", "Projection:  0  angle: 0.0", "counts before: 12345", "counts_after: 45678"],
        ["timestamp", "Projection:  1  angle: 0.1", "counts before: 45678", "counts_after: 84678"],
        ["timestamp", "Projection:  2  angle: 0.2", "counts before: 84678", "counts_after: 124333"],
    ]
    logfile = IMATLogFile(test_input)
    assert len(logfile.counts().value) == 3
    assert logfile.counts().value[0] == 45678 - 12345
    assert logfile.counts().value[1] == 84678 - 45678
    assert logfile.counts().value[2] == 124333 - 84678


def assert_raises(exc_type, callable, *args, **kwargs):
    try:
        callable(*args, **kwargs)
        assert False, "Did not raise"
    except exc_type:
        return
    except Exception:
        assert False, "Did not raise expected exception."


def test_find_missing_projection_number():
    test_input = [
        ["ignored line"],
        ["ignored line"],
        ["timestamp", "Projection:  0  angle: 0.0", "counts before: 12345", "counts_after: 45678"],
        ["timestamp", "Projection:  1  angle: 0.1", "counts before: 12345", "counts_after: 45678"],
        ["timestamp", "Projection:  2  angle: 0.2", "counts before: 12345", "counts_after: 45678"],
    ]
    logfile = IMATLogFile(test_input)
    assert len(logfile.projection_numbers()) == 3
    # nothing missing
    logfile.raise_if_angle_missing(["file_000.tif", "file_001.tif", "file_002.tif"])
    # image file missing
    assert_raises(RuntimeError, logfile.raise_if_angle_missing, ["file_000.tif", "file_002.tif"])
    # image file missing
    assert_raises(RuntimeError, logfile.raise_if_angle_missing, ["file_000.tif", "file_001.tif"])
    assert_raises(RuntimeError, logfile.raise_if_angle_missing,
                  ["file_000.tif", "file_001.tif", "file_002.tif", "file_003.tif"])
