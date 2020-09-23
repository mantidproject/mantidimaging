import numpy as np

from mantidimaging.core.utility.imat_log_file_parser import IMATLogFile


def test_parsing_log_file():
    test_input = [["ignored line"], ["ignored line"],
                  ["timestamp", "projection index and angle: 0.100", "counts before: 12345", "counts_after: 45678"]]
    logfile = IMATLogFile(test_input)
    assert len(logfile.projection_angles().value) == 1
    assert logfile.projection_angles().value[0] == np.deg2rad(0.1), f"Got: {logfile.projection_angles().value[0]}"
    assert logfile.counts().value[0] == (45678 - 12345)
