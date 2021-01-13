# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from mantidimaging.core.utility.imat_log_file_parser import CSVLogParser, IMATLogFile, TextLogParser


def generate_txt_logfile() -> IMATLogFile:
    data = [
        TextLogParser.EXPECTED_HEADER_FOR_IMAT_TEXT_LOG_FILE,  # checked if exists, but skipped
        "",  # skipped when parsing
        # for each row a list with 4 entries is currently expected
        "Sun Feb 10 00:22:04 2019   Projection:  0  angle: 0.0   Monitor 3 before:  4577907   Monitor 3 after:  4720271",  # noqa: E501
        "Sun Feb 10 00:22:37 2019   Projection:  1  angle: 0.3152   Monitor 3 before:  4729337   Monitor 3 after:  4871319",  # noqa: E501
        "Sun Feb 10 00:23:10 2019   Projection:  2  angle: 0.6304   Monitor 3 before:  4879923   Monitor 3 after:  5022689",  # noqa: E501
        "Sun Feb 10 00:23:43 2019   Projection:  3  angle: 0.9456   Monitor 3 before:  5031423   Monitor 3 after:  5172216",  # noqa: E501
        "Sun Feb 10 00:24:16 2019   Projection:  4  angle: 1.2608   Monitor 3 before:  5180904   Monitor 3 after:  5322691",  # noqa: E501
        "Sun Feb 10 00:24:49 2019   Projection:  5  angle: 1.576   Monitor 3 before:  5334225   Monitor 3 after:  5475239",  # noqa: E501
        "Sun Feb 10 00:25:22 2019   Projection:  6  angle: 1.8912   Monitor 3 before:  5483964   Monitor 3 after:  5626608",  # noqa: E501
        "Sun Feb 10 00:25:55 2019   Projection:  7  angle: 2.2064   Monitor 3 before:  5635673   Monitor 3 after:  5777316",  # noqa: E501
        "Sun Feb 10 00:26:29 2019   Projection:  8  angle: 2.5216   Monitor 3 before:  5786535   Monitor 3 after:  5929002",  # noqa: E501
        "Sun Feb 10 00:27:02 2019   Projection:  9  angle: 2.8368   Monitor 3 before:  5938142   Monitor 3 after:  6078866",  # noqa: E501
    ]
    return IMATLogFile(data, "/tmp/fake")


def generate_csv_logfile() -> IMATLogFile:
    data = [
        CSVLogParser.EXPECTED_HEADER_FOR_IMAT_CSV_LOG_FILE,
        "Sun Feb 10 00:22:04 2019,Projection,0,angle: 0.0,Monitor 3 before: 4577907,Monitor 3 after:  4720271",
        "Sun Feb 10 00:22:37 2019,Projection,1,angle: 0.3152,Monitor 3 before: 4729337,Monitor 3 after:  4871319",
        "Sun Feb 10 00:23:10 2019,Projection,2,angle: 0.6304,Monitor 3 before: 4879923,Monitor 3 after:  5022689",
        "Sun Feb 10 00:23:43 2019,Projection,3,angle: 0.9456,Monitor 3 before: 5031423,Monitor 3 after:  5172216",
        "Sun Feb 10 00:24:16 2019,Projection,4,angle: 1.2608,Monitor 3 before: 5180904,Monitor 3 after:  5322691",
        "Sun Feb 10 00:24:49 2019,Projection,5,angle: 1.576,Monitor 3 before: 5334225,Monitor 3 after:  5475239",
        "Sun Feb 10 00:25:22 2019,Projection,6,angle: 1.8912,Monitor 3 before: 5483964,Monitor 3 after:  5626608",
        "Sun Feb 10 00:25:55 2019,Projection,7,angle: 2.2064,Monitor 3 before: 5635673,Monitor 3 after:  5777316",
        "Sun Feb 10 00:26:29 2019,Projection,8,angle: 2.5216,Monitor 3 before: 5786535,Monitor 3 after:  5929002",
        "Sun Feb 10 00:27:02 2019,Projection,9,angle: 2.8368,Monitor 3 before: 5938142,Monitor 3 after:  6078866",
    ]
    return IMATLogFile(data, "/tmp/fake")
