# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np


def execute(data_length: int, slice_ids: np.ndarray, cors_for_sinograms: np.ndarray) -> np.ndarray:
    """
    Interpolates the Centers of Rotation for the sinograms that are not
    provided.

    This expects CORs for only a few sinograms and will interpolate the rest,
    so that every single sinogram has an associated COR with it.

    This technique has so far produced good results, when using Tomopy to do
    the reconstruction.

    :param data_length: The length of the data along the axis we're traversing.
                        E.g. the number of images

    :param slice_ids: The slice IDs for which we are passing the corresponding
                      CORs

    :param cors_for_sinograms: The CORs for the sinograms

    :returns: A np.array with length equal to data_length containing the
              interpolated CORs.
    """
    assert cors_for_sinograms and all(
        isinstance(cor, float) for cor in cors_for_sinograms), \
        "The centers of rotation MUST be floats"

    assert slice_ids and all(isinstance(slice, int) for slice in slice_ids), \
        "The sinograms associated with the centers of rotation MUST be ints"

    return np.interp(list(range(data_length)), slice_ids, cors_for_sinograms)
