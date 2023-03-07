# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import glob
import itertools
import os
import numpy as np
from logging import getLogger
from typing import List, Optional, Tuple

log = getLogger(__name__)

DEFAULT_IO_FILE_FORMAT = 'tif'

SIMILAR_FILE_EXTENSIONS = (('tif', 'tiff'), ('fit', 'fits'))

THRESHOLD_180 = np.radians(1)


def get_candidate_file_extensions(ext: str) -> List[str]:
    """
    Gets a list of file extensions which can be used to load files.
    :param ext: User provided file extension
    :returns: List of extensions in the order they should be tested
    """
    # Get all tuples of similar extensions that the provided extension appears
    # in
    similar_extensions = [e for e in SIMILAR_FILE_EXTENSIONS if ext in e]

    # Concatenate them all into a single list
    candidates = list(itertools.chain(*similar_extensions))

    # Remove the provided extension from the list
    if ext in candidates:
        candidates.remove(ext)

    # Return candidates, provided extension is always first to give it priority
    return [ext] + candidates


def find_first_file_that_is_possibly_a_sample(file_path: str) -> Optional[str]:
    # Grab all .tif or .tiff files
    possible_files = glob.glob(os.path.join(file_path, "**/*.tif*"), recursive=True)

    for possible_file in sorted(possible_files):
        lower_filename = os.path.basename(possible_file).lower()
        if "flat" not in lower_filename and "dark" not in lower_filename and "180" not in lower_filename:
            return possible_file
    return None


def find_projection_closest_to_180(projections: np.ndarray, projection_angles: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Finds the projection closest to 180 and returns it with the difference.
    :param projections: The array of projection images.
    :param projection_angles: The array of projection angles.
    :return: The 180 projection/the closest non-180 projection and the difference between its angle and 180.
    """
    diff = np.abs(projection_angles - np.pi)
    return projections[diff.argmin()], np.amin(diff)
