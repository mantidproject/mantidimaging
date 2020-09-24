from logging import getLogger
from typing import Tuple

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.parallel import utility as pu, two_shared_mem as ptsm
from mantidimaging.core.utility.data_containers import Degrees, ScalarCoR
from mantidimaging.core.utility.progress_reporting import Progress

LOG = getLogger(__name__)


def do_search(row: int, image_width, p0, p180, search_range: list) -> int:
    minimum = 1e7
    index_min = 0
    for t in search_range:
        rmse = np.square(np.roll(p0[row], t, axis=0) - p180[row]).sum() / image_width
        if rmse <= minimum:
            minimum = rmse
            index_min = t
    return index_min


def do_search2d(store, search_index, p0_and_180, image_width):
    # calculates squared sum error in the difference between the images
    store[:] = np.square(np.roll(p0_and_180[0], search_index, axis=1) - p0_and_180[1]).sum(axis=1) / image_width


# find the actual search_range used for fitting with
# row = 450
# search_range[np.where(store.T[row] == store.T[row].min())[0][0]]
# originally the data is stored in dimensions
# corresponding to (search_range, square sum)
# we transpose store with store.T to make the array hold
# (square sum, search range) so that each store.T[row] accesses the
# information for the row's square sum across all search ranges
# then we just find the index of the minimum one (minimum error)
# and we get which search range is at that index
# that is the number that we then pass into polyfit
#
# def find_center(images: Images, progress: Progress) -> Tuple[ScalarCoR, Degrees]:
#     # assume the ROI is the full image, i.e. the slices are ALL rows of the image
#     slices = np.arange(images.height)
#     with pu.temp_shared_array((images.height, )) as shift:
#         # this is the area that is looked into for the shift after overlapping the images
#         search_range = get_search_range(images.width)
#
#         func = shared_mem.create_partial(do_search,
#                                          shared_mem.fwd_index_only,
#                                          image_width=images.width,
#                                          p0=images.projection(0),
#                                          p180=np.fliplr(images.proj180deg.data[0]),
#                                          search_range=search_range)
#         shared_mem.execute(shift, func, progress=progress, msg="Finding correlation on row")
#         par = np.polyfit(slices, shift, deg=1)
#         m = par[0]
#         q = par[1]
#         LOG.debug(f"m={m}, q={q}")
#         theta = Degrees(np.rad2deg(np.arctan(0.5 * m)))
#         offset = np.round(m * images.height * 0.5 + q) * 0.5
#         LOG.info(f"found offset: {-offset} and tilt {theta}")
#         return ScalarCoR(images.h_middle + -offset), theta

def find_center(images: Images, progress: Progress) -> Tuple[ScalarCoR, Degrees]:
    # assume the ROI is the full image, i.e. the slices are ALL rows of the image
    slices = np.arange(images.height)
    with pu.temp_shared_array((images.height,)) as shift:
        search_range = get_search_range(images.width)
        with pu.temp_shared_array((len(search_range), images.height)) as store:
            with pu.temp_shared_array((len(search_range),), dtype=np.int32) as shared_search_range:
                # share the projections to avoid copying between
                with pu.temp_shared_array((2, images.height, images.width)) as shared_projections:
                    shared_projections[0][:] = images.projection(0)
                    shared_projections[1][:] = np.fliplr(images.proj180deg.data[0])
                    shared_search_range[:] = np.asarray(search_range, dtype=np.int32)

                    func = ptsm.create_partial(do_search2d,
                                               ptsm.inplace3,
                                               image_width=images.width)
                    ptsm.execute(store, shared_search_range, func, progress=progress, msg="Finding correlation on row",
                                 third_data=shared_projections)

                for row in range(images.height):
                    shift[row] = search_range[np.where(store.T[row] == store.T[row].min())[0][0]]

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
