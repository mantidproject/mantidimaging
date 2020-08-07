from logging import getLogger
from typing import Tuple

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.parallel import shared_mem
from mantidimaging.core.utility.data_containers import Degrees, ScalarCoR

LOG = getLogger(__name__)


def do_search(row: int, image_width, p0, p180, search_range: list) -> int:
    minimum = 1e7
    index_min = 0
    for t in search_range:
        rmse = np.square((np.roll(p0[row], t, axis=0) - p180[row])).sum() / image_width
        if rmse <= minimum:
            minimum = rmse
            index_min = t
    return index_min


def find_center(images: Images) -> Tuple[ScalarCoR, Degrees]:
    # p0 = images.projection(0)
    # p180 = np.fliplr(images.projection(images.num_projections // 2))

    # assume the ROI is the full image, i.e. the slices are ALL rows of the image
    slices = np.arange(images.height)
    shift = np.zeros(images.height)

    # this is the area that is looked into for the shift after overlapping the images
    tmin = -images.width // 2
    tmax = images.width - images.width // 2
    search_range = range(tmin, tmax + 1)

    func = shared_mem.create_partial(do_search, shared_mem.fwd_index_only,
                                     image_width=images.width,
                                     p0=images.projection(0),
                                     p180=np.fliplr(images.projection(images.num_projections // 2)),
                                     search_range=search_range)
    shared_mem.execute(shift, func, msg="Finding COR correlation")
    print(shift)
    # for row in slices:
    #     minimum = 1e7
    #     index_min = 0
    #
    #     for t in search_range:
    #         rmse = np.square((np.roll(p0[row], t, axis=0) - p180[row])).sum() / images.width
    #         if rmse <= minimum:
    #             minimum = rmse
    #             index_min = t
    #
    #     shift[row] = index_min

    par = np.polyfit(slices, shift, deg=1)
    m = par[0]
    q = par[1]
    LOG.debug(f"m={m}, q={q}")
    theta = Degrees(np.rad2deg(np.arctan(0.5 * m)))
    offset = np.round(m * images.height * 0.5 + q) * 0.5
    LOG.info(f"found offset: {-offset} and tilt {theta}")
    return ScalarCoR(images.h_middle + -offset), theta
