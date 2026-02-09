# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from logging import getLogger
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from mantidimaging.core.parallel import utility as pu, shared as ps
from mantidimaging.core.utility.data_containers import Degrees, ScalarCoR

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack
    from mantidimaging.core.utility.progress_reporting import Progress

LOG = getLogger(__name__)


def do_calculate_correlation_err(store, search_index: int, p0_and_180, image_width: int) -> None:
    """
    Calculates squared sum error in the difference between the projection at 0 degrees, and the one at 180 degrees
    """
    store[:] = np.square(np.roll(p0_and_180[0], search_index, axis=1) - p0_and_180[1]).sum(axis=1) / image_width


def find_center(images: ImageStack,
                progress: Progress,
                use_projections: tuple[int, int] | None = None) -> tuple[ScalarCoR, Degrees]:

    if images is None:
        raise ValueError("images cannot be None")

    if use_projections is not None:
        start_idx, end_idx = use_projections
        proj_a = images.projection(start_idx)
        proj_b = np.fliplr(images.projection(end_idx))
        LOG.info(f"Using projections {start_idx} and {end_idx} for correlation")
    else:
        raise ValueError("You must specify use_projections (tuple of projection indices) for correlation.")

    # Assume the ROI is the full image, i.e. the slices are ALL rows of the image
    slices = np.arange(images.height)
    shift = pu.create_array((images.height, ), dtype=np.float32)
    search_range = get_search_range(images.width)
    min_correlation_error = pu.create_array((len(search_range), images.height), dtype=np.float32)
    shared_search_range = pu.create_array((len(search_range), ), dtype=np.int32)
    shared_search_range.array[:] = np.asarray(search_range, dtype=np.int32)

    # Copy projections to shared memory
    shared_projections = pu.create_array((2, images.height, images.width), dtype=np.float32)
    shared_projections.array[0][:] = proj_a
    shared_projections.array[1][:] = proj_b

    # Prepare parameters for the compute function
    params = {'image_width': images.width}
    ps.run_compute_func(compute_correlation_error,
                        len(search_range), [min_correlation_error, shared_projections, shared_search_range],
                        params,
                        progress=progress)
    _find_shift(images, search_range, min_correlation_error.array, shift.array)

    par = np.polyfit(slices, shift.array, deg=1)
    m, q = float(par[0]), float(par[1])
    theta = Degrees(np.rad2deg(np.arctan(0.5 * m)))
    offset = float(np.round(m * images.height * 0.5 + q) * 0.5)
    LOG.info(f"found offset: {-offset} and tilt {theta}")

    return ScalarCoR(images.h_middle - offset), theta


def compute_correlation_error(index: int, arrays: list[NDArray[np.float32]], params: dict[str, int]) -> None:
    min_correlation_error = arrays[0]
    shared_projections = arrays[1]
    shared_search_range = arrays[2]
    image_width = params['image_width']

    search_index = int(shared_search_range[index])
    do_calculate_correlation_err(min_correlation_error[index], search_index,
                                 (shared_projections[0], shared_projections[1]), image_width)


def _find_shift(images: ImageStack, search_range: range, min_correlation_error: NDArray[np.float32],
                shift: NDArray[np.float32]) -> NDArray[np.float32]:
    # Then we just find the index of the minimum one (minimum error)
    min_correlation_error = np.transpose(min_correlation_error)
    # argmin returns a list of where the minimum argument is found
    # just in case that happens - get the first minimum one, should be close enough
    for row in range(images.height):
        min_arg_positions = int(min_correlation_error[row].argmin())
        # And we get which search range is at that index
        # that is the number that we then pass into polyfit
        shift[row] = search_range[min_arg_positions]

    return shift


def get_search_range(width: int) -> range:
    tmin = -width // 2
    tmax = width - width // 2
    search_range = range(tmin, tmax + 1)
    return search_range
