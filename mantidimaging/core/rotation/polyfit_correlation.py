from logging import getLogger
from typing import Tuple

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.parallel import utility as pu, shared as ps
from mantidimaging.core.utility.data_containers import Degrees, ScalarCoR
from mantidimaging.core.utility.progress_reporting import Progress

LOG = getLogger(__name__)


def do_search(store: np.ndarray, search_index: int, p0_and_180: Tuple[np.ndarray, np.ndarray], image_width: int):
    """
    Calculates squared sum error in the difference between the projection at 0 degrees, and the one at 180 degrees
    """
    store[:] = np.square(np.roll(p0_and_180[0], search_index, axis=1) - p0_and_180[1]).sum(axis=1) / image_width


def find_center(images: Images, progress: Progress) -> Tuple[ScalarCoR, Degrees]:
    # assume the ROI is the full image, i.e. the slices are ALL rows of the image
    slices = np.arange(images.height)
    with pu.temp_shared_array((images.height, )) as shift:
        search_range = get_search_range(images.width)
        with pu.temp_shared_array((len(search_range), images.height)) as store:
            with pu.temp_shared_array((len(search_range), ), dtype=np.int32) as shared_search_range:
                shared_search_range[:] = np.asarray(search_range, dtype=np.int32)
                # if the projections are passed in the partial they are copied to every process on every iteration
                # this makes the multiprocessing significantly slower
                # so they are copied into a shared array to avoid that copying
                with pu.temp_shared_array((2, images.height, images.width)) as shared_projections:
                    shared_projections[0][:] = images.projection(0)
                    shared_projections[1][:] = np.fliplr(images.proj180deg.data[0])

                    do_search_partial = ps.create_partial(do_search, ps.inplace3, image_width=images.width)

                    ps.shared_list = [store, shared_search_range, shared_projections]
                    ps.execute(do_search_partial,
                               num_operations=store.shape[0],
                               progress=progress,
                               msg="Finding correlation on row")

            # Originally the output of do_search is stored in dimensions
            # corresponding to (search_range, square sum). This is awkward to navigate
            # we transpose store to make the array hold (square sum, search range)
            # so that each store[row] accesses the information for the row's square sum across all search ranges
            store = np.transpose(store)
            for row in range(images.height):
                # then we just find the index of the minimum one (minimum error)
                min_error_position = np.where(store[row] == store[row].min())[0][0]
                # and we get which search range is at that index
                # that is the number that we then pass into polyfit
                shift[row] = search_range[min_error_position]

            par = np.polyfit(slices, shift, deg=1)
            m = par[0]
            q = par[1]
            LOG.debug(f"m={m}, q={q}")
            theta = Degrees(np.rad2deg(np.arctan(0.5 * m)))
            offset = np.round(m * images.height * 0.5 + q) * 0.5
            LOG.info(f"found offset: {-offset} and tilt {theta}")
            return ScalarCoR(images.h_middle + -offset), theta


def get_search_range(width):
    tmin = -width // 2
    tmax = width - width // 2
    search_range = range(tmin, tmax + 1)
    return search_range
