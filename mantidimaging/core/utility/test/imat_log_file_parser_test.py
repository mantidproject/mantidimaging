from mantidimaging.core.utility.imat_log_file_parser import IMATLogFile


def test_parsing_log_file():
    input = [["ignored line"], ["ignored line"],
             ["timestamp", "projection index and angle: 0.000", "counts before", "counts_after"]]
    logfile = IMATLogFile(input)
    assert logfile.projection_angles().value == [0.000]
