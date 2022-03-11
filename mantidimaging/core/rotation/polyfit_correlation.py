# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from logging import getLogger
from typing import Tuple

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.parallel import utility as pu, shared as ps
from mantidimaging.core.utility.data_containers import Degrees, ScalarCoR
from mantidimaging.core.utility.progress_reporting import Progress

LOG = getLogger(__name__)


def do_calculate_correlation_err(store: np.ndarray, search_index: int, p0_and_180: Tuple[np.ndarray, np.ndarray],
                                 image_width: int):
    """
    Calculates squared sum error in the difference between the projection at 0 degrees, and the one at 180 degrees
    """
    store[:] = np.square(np.roll(p0_and_180[0], search_index, axis=1) - p0_and_180[1]).sum(axis=1) / image_width


def find_center(images: ImageStack, progress: Progress) -> Tuple[ScalarCoR, Degrees]:
    # assume the ROI is the full image, i.e. the slices are ALL rows of the image
    slices = np.arange(images.height)
    shift = pu.create_array((images.height, ))

    search_range = get_search_range(images.width)
    min_correlation_error = pu.create_array((len(search_range), images.height))
    shared_search_range = pu.create_array((len(search_range), ), dtype=np.int32)
    shared_search_range[:] = np.asarray(search_range, dtype=np.int32)
    _calculate_correlation_error(images, shared_search_range, min_correlation_error, progress)

    # Originally the output of do_search is stored in dimensions
    # corresponding to (search_range, square sum). This is awkward to navigate
    # we transpose store to make the array hold (square sum, search range)
    # so that each store[row] accesses the information for the row's square sum across all search ranges
    _find_shift(images, search_range, min_correlation_error, shift)

    par = np.polyfit(slices, shift, deg=1)
    m = par[0]
    q = par[1]
    LOG.debug(f"m={m}, q={q}")
    theta = Degrees(np.rad2deg(np.arctan(0.5 * m)))
    offset = np.round(m * images.height * 0.5 + q) * 0.5
    LOG.info(f"found offset: {-offset} and tilt {theta}")
    return ScalarCoR(images.h_middle + -offset), theta


def _calculate_correlation_error(images, shared_search_range, min_correlation_error, progress):
    # if the projections are passed in the partial they are copied to every process on every iteration
    # this makes the multiprocessing significantly slower
    # so they are copied into a shared array to avoid that copying
    shared_projections = pu.create_array((2, images.height, images.width))
    shared_projections[0][:] = images.projection(0)
    shared_projections[1][:] = np.fliplr(images.proj180deg.data[0])

    do_search_partial = ps.create_partial(do_calculate_correlation_err, ps.inplace3, image_width=images.width)

    ps.shared_list = [min_correlation_error, shared_search_range, shared_projections]
    ps.execute(do_search_partial,
               num_operations=min_correlation_error.shape[0],
               progress=progress,
               msg="Finding correlation on row")


def _find_shift(images: ImageStack, search_range: range, min_correlation_error: np.ndarray, shift: np.ndarray):
    min_correlation_error = np.transpose(min_correlation_error)
    for row in range(images.height):
        # then we just find the index of the minimum one (minimum error)
        min_arg_positions = min_correlation_error[row].argmin()
        # argmin returns a list of where the minimum argument is found
        # just in case that happens - get the first minimum one, should be close enough
        min_arg = min_arg_positions if isinstance(min_arg_positions, np.int64) else min_arg_positions[0]
        # and we get which search range is at that index
        # that is the number that we then pass into polyfit
        shift[row] = search_range[min_arg]


def get_search_range(width):
    tmin = -width // 2
    tmax = width - width // 2
    search_range = range(tmin, tmax + 1)
    return search_range
