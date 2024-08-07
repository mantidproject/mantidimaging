# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from logging import getLogger
from typing import TYPE_CHECKING, Any

import numpy as np

from mantidimaging.core.parallel import utility as pu, shared as ps
from mantidimaging.core.utility.data_containers import Degrees, ScalarCoR

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack
    from mantidimaging.core.utility.progress_reporting import Progress

LOG = getLogger(__name__)


def do_calculate_correlation_err(store: np.ndarray, search_index: int, p0_and_180: tuple[np.ndarray, np.ndarray],
                                 image_width: int) -> None:
    """
    Calculates squared sum error in the difference between the projection at 0 degrees, and the one at 180 degrees
    """
    store[:] = np.square(np.roll(p0_and_180[0], search_index, axis=1) - p0_and_180[1]).sum(axis=1) / image_width


def find_center(images: ImageStack, progress: Progress) -> tuple[ScalarCoR, Degrees]:
    if images is None or images.proj180deg is None:
        raise ValueError("images and images.proj180deg cannot be None")

    # Assume the ROI is the full image, i.e. the slices are ALL rows of the image
    slices = np.arange(images.height)
    shift = pu.create_array((images.height, ), dtype=np.float32)
    search_range = get_search_range(images.width)
    min_correlation_error = pu.create_array((len(search_range), images.height), dtype=np.float32)
    shared_search_range = pu.create_array((len(search_range), ), dtype=np.int32)
    shared_search_range.array[:] = np.asarray(search_range, dtype=np.int32)

    # Copy projections to shared memory
    shared_projections = pu.create_array((2, images.height, images.width), dtype=np.float32)
    shared_projections.array[0][:] = images.projection(0)
    shared_projections.array[1][:] = np.fliplr(images.proj180deg.data[0])

    # Prepare parameters for the compute function
    params = {
        'image_width': images.width,
    }
    ps.run_compute_func(compute_correlation_error,
                        len(search_range), [min_correlation_error, shared_projections, shared_search_range],
                        params,
                        progress=progress)

    # Originally the output of do_search is stored in dimensions
    # corresponding to (search_range, square sum). This is awkward to navigate
    # we transpose store to make the array hold (square sum, search range)
    # so that each store[row] accesses the information for the row's square sum across all search ranges
    _find_shift(images, search_range, min_correlation_error.array, shift.array)

    par = np.polyfit(slices, shift.array, deg=1)
    m = par[0]
    q = par[1]
    LOG.debug(f"m={m}, q={q}")

    theta = Degrees(np.rad2deg(np.arctan(0.5 * m)))
    offset = np.round(m * images.height * 0.5 + q) * 0.5
    LOG.info(f"found offset: {-offset} and tilt {theta}")

    return ScalarCoR(images.h_middle + -offset), theta


def compute_correlation_error(index: int, arrays: list[Any], params: dict[str, Any]) -> None:
    min_correlation_error = arrays[0]
    shared_projections = arrays[1]
    shared_search_range = arrays[2]
    image_width = params['image_width']

    search_index = shared_search_range[index]
    do_calculate_correlation_err(min_correlation_error[index], search_index,
                                 (shared_projections[0], shared_projections[1]), image_width)


def _find_shift(images: ImageStack, search_range: range, min_correlation_error: np.ndarray,
                shift: np.ndarray) -> np.ndarray:
    # Then we just find the index of the minimum one (minimum error)
    min_correlation_error = np.transpose(min_correlation_error)
    # argmin returns a list of where the minimum argument is found
    # just in case that happens - get the first minimum one, should be close enough
    for row in range(images.height):
        min_arg_positions = min_correlation_error[row].argmin()
        min_arg = min_arg_positions if isinstance(min_arg_positions, np.int64) else min_arg_positions[0]
        # And we get which search range is at that index
        # that is the number that we then pass into polyfit
        shift[row] = search_range[min_arg]

    return shift


def get_search_range(width: int) -> range:
    tmin = -width // 2
    tmax = width - width // 2
    search_range = range(tmin, tmax + 1)
    return search_range
