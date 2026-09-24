# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

# yapf: disable
IMAT_2023_SPECTRA_LOG = [
    "IMAT00003717_Brass_sphere_d99mm_000_Spectra.txt",
"""0.012	334937
0.012041	331913
0.0120819	331737
0.0121229	331161
"""
]

IMAT_2019_TOMO_LOG = [
    "TomoIMAT00010675_FlowerFine_log.txt",
""" TIME STAMP  IMAGE TYPE   IMAGE COUNTER   COUNTS BM3 before image   COUNTS BM3 after image

Sun Feb 10 00:22:04 2019   Projection:  0  angle: 0.0   Monitor 3 before:  4577907   Monitor 3 after:  4720271
Sun Feb 10 00:22:37 2019   Projection:  1  angle: 0.3152   Monitor 3 before:  4729337   Monitor 3 after:  4871319
Sun Feb 10 00:23:10 2019   Projection:  2  angle: 0.6304   Monitor 3 before:  4879923   Monitor 3 after:  5022689
Sun Feb 10 00:23:43 2019   Projection:  3  angle: 0.9456   Monitor 3 before:  5031423   Monitor 3 after:  5172216
"""
]

INVALID_FILE = [
    "foo.txt",
"""aaa
bbb ccc
"""
]

CSV_SAMPLE_LOG = [
    "sample_log.csv",
"""TIME STAMP,IMAGE TYPE,IMAGE COUNTER,PROJECTION ANGLE DEG,COUNTS BEFORE,COUNTS AFTER
Tue Nov 15 19:58:17 2022,Projection,0,0.0,12588,145908
Tue Nov 15 19:58:50 2022,Projection,1,0.3152,145910,279015
Tue Nov 15 19:59:23 2022,Projection,2,0.6304,279020,412500
Tue Nov 15 19:59:56 2022,Projection,3,0.9456,412510,545900
"""
]

CSV_SAMPLE_LOG_EXTRA_COLUMNS = [
    "sample_log_more_cols.csv",
"""TIME STAMP,IMAGE TYPE,IMAGE COUNTER,PROJECTION ANGLE DEG,COUNTS BEFORE,COUNTS AFTER,PIXEL SIZE,TEMPERATURE
Tue Nov 15 19:58:17 2022,Projection,0,0.0,12588,145908,29.0,22
Tue Nov 15 19:58:50 2022,Projection,1,0.3152,145910,279015,29.0,22.02
Tue Nov 15 19:59:23 2022,Projection,2,0.6304,279020,412500,29.0,22.03
Tue Nov 15 19:59:56 2022,Projection,3,0.9456,412510,545900,29.0,22.05
"""
]

CSV_MINIMAL_COLUMNS = [
    "sample_log_one_col.csv",
"""IMAGE COUNTER
0
1
2
3
"""
]
