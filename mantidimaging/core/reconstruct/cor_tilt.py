from __future__ import absolute_import, division, print_function

from logging import getLogger

import numpy as np
import scipy as sp

from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.filters.crop_coords import execute_single as crop

# This import is used to provide the available() function which is used to
# check if the functionality of a module is available based on the presence of
# optional libraries
from mantidimaging.core.utility.optional_imports import (  # noqa: F401
        safe_import,
        tomopy_available as available)

tomopy = safe_import('tomopy')


def find_cor_at_slice(sample_data, slice_idx):
    return tomopy.find_center_vo(
          tomo=sample_data,
          ind=slice_idx,
          ratio=1.0,
          smin=0,
          smax=200,
          srad=10,
          step=2,
          drop=0)


def calculate_cor_and_tilt(sample_data, roi, indices, progress=None):
    """
    :param sample_data: Full image stack
    :param roi: Region of interest from which to calculate CORs
    :param indices: Indices of slices to calculate CORs (in full image
                    coordinates)
    :param progress: Progress reporting instance
    """
    log = getLogger(__name__)

    progress = Progress.ensure_instance(progress)
    progress.task_name = "Find COR and tilt"
    progress.add_estimated_steps(2 + indices.size)

    with progress:
        # Crop to the ROI from which the COR/tilt are calculated
        progress.update(msg="Crop to ROI")
        cropped_data = crop(sample_data,
                            region_of_interest=roi,
                            progress=progress)
        log.debug("Cropped data shape: {}".format(cropped_data.shape))

        # Indices relative to the top of the ROI in image order (top zero)
        indices_in_roi = indices - roi[1]

        # Flip the Y coordinates so that 0 is the bottom of the sample
        # This allows us to take the Y intercept from the linear regression as
        # the COR
        indices_in_roi_flipped = cropped_data.shape[1] - indices_in_roi
        fliped_data = np.flip(cropped_data, 1)

        # Obtain COR for each desired slice of ROI
        cors = []
        for idx in indices_in_roi_flipped:
            progress.update(msg="COR at slice {}".format(idx))
            cor = find_cor_at_slice(fliped_data, idx)
            cors.append((idx, cor))

        # Collect data in Numpy array
        cors = np.asarray(cors)
        slices, cors = cors[:, 0], cors[:, 1]

        # Perform linear regression of calculated CORs against slice index
        progress.update(msg="Linear regression")
        m, cor = sp.stats.linregress(slices, cors)[:2]
        log.debug("m={}, c={}".format(m, cor))

        # Offset COR for ROI
        cor += roi[0]
        cors += roi[0]

        # Caulcuate tilt angle
        hyp = slices[-1]
        adj = (m * slices[-1])
        opp = np.sqrt(hyp ** 2 + adj ** 2)
        tilt = np.arcsin(adj / opp)

        log.info("COR={}, tilt={} ({}deg)".format(cor, tilt, np.rad2deg(tilt)))

    return tilt, cor, slices, cors, m
