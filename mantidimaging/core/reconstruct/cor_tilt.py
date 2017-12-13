from __future__ import absolute_import, division, print_function

from logging import getLogger

import math

import numpy as np
import scipy as sp

from mantidimaging.core.data import const
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.filters.crop_coords import execute_single as crop

# This import is used to provide the available() function which is used to
# check if the functionality of a module is available based on the presence of
# optional libraries
from mantidimaging.core.utility.optional_imports import (  # noqa: F401
        tomopy_available as available)

import mantidimaging.external.tomopy_rotation as rotation


def find_cor_at_slice(slice_idx, sample_data):
    return rotation.find_center_vo(
          tomo=sample_data,
          ind=slice_idx,
          ratio=1.0,
          smin=0,
          smax=200,
          srad=10.0,
          step=2.0,
          drop=0)


def calculate_cor_and_tilt(
        stack, roi, indices, cores=None, progress=None):
    """
    :param stack: Full image stack
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
        cropped_data = crop(stack.sample,
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
        cors = pu.create_shared_array(
                indices_in_roi_flipped.shape,
                indices_in_roi_flipped.dtype)
        np.copyto(cors, indices_in_roi_flipped)

        f = psm.create_partial(find_cor_at_slice,
                               fwd_func=psm.return_fwd_func,
                               sample_data=fliped_data)

        psm.execute(cors, f, cores=cores)

        slices = indices_in_roi_flipped

        # Perform linear regression of calculated CORs against slice index
        progress.update(msg="Linear regression")
        m, cor = sp.stats.linregress(slices, cors)[:2]
        log.debug("m={}, c={}".format(m, cor))

        # Offset COR for ROI
        cor += roi[0]
        cors += roi[0]

        # Calculate tilt angle
        tilt = cors_to_tilt_angle(slices[-1], m)

        log.info("COR={}, tilt={} ({}deg)".format(cor, tilt, np.rad2deg(tilt)))

        # Record results in stack properties
        stack.properties[const.AUTO_COR_TILT] = {
            'rotation_centre': cor,
            'tilt_angle_rad': tilt,
            'fitted_gradient': m,
            'slice_indices': slices.tolist(),
            'rotation_centres': cors.tolist()
        }

    return tilt, cor, slices, cors, m


def cors_to_tilt_angle(slice_upper, m):
    adj = slice_upper
    opp = m * slice_upper
    hyp = np.sqrt(adj ** 2 + opp ** 2)
    return np.arcsin(opp / hyp)


def tilt_angle_to_cors(theta, cor_zero, slice_range):
    # Calculate max COR
    adj = slice_range[-1] - slice_range[0]
    adj_a = (math.pi / 2) - theta
    cor_max = ((adj / np.sin(adj_a)) * np.sin(theta)) + cor_zero

    # Interpolate COR over range
    interpolated_cors = np.interp(
            slice_range,
            np.linspace(slice_range[0], slice_range[-1], 2),
            np.asarray([cor_zero, cor_max]))

    return interpolated_cors
