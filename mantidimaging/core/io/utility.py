# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from pathlib import Path

import numpy as np
from logging import getLogger

log = getLogger(__name__)

DEFAULT_IO_FILE_FORMAT = 'tif'
NEXUS_PROCESSED_DATA_PATH = 'processed-data'

THRESHOLD_180 = np.radians(1)


def find_first_file_that_is_possibly_a_sample(file_path: Path) -> Path | None:
    """
    Finds the first file that is possibly a tif, .tiff, .fit or .fits sample file.
    If files are found, the files are sorted and filtered based on name and returned.
    """
    file_types = ['tif', 'tiff', 'fit', 'fits']
    for ext in file_types:
        possible_files = list(file_path.rglob(f'*.{ext}'))
        if possible_files:
            for possible_file in sorted(possible_files):
                lower_filename = possible_file.name.lower()
                if 'flat' not in lower_filename and 'dark' not in lower_filename and '180' not in lower_filename:
                    return possible_file
    return None
