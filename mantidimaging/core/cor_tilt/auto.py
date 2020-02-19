from logging import getLogger

import numpy as np

from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress

# This import is used to provide the available() function which is used to
# check if the functionality of a module is available based on the presence of
# optional libraries
from mantidimaging.core.utility.optional_imports import (  # noqa: F401
    safe_import, tomopy_available as available)

tomopy = safe_import('tomopy')

LOG = getLogger(__name__)


def find_cor_at_slice(slice_idx, sample_data):
    return tomopy.find_center_vo(tomo=sample_data,
                                 ind=slice_idx,
                                 ratio=1.0,
                                 smin=0,
                                 smax=200,
                                 srad=10.0,
                                 step=2.0,
                                 drop=0)


def auto_find_cors(stack, roi, model, projections=None, cores=None, progress=None):
    if model.empty:
        raise ValueError('No points in model to calculate')

    progress = Progress.ensure_instance(progress)
    progress.task_name = "Auto find CORs"
    progress.add_estimated_steps(2 + model.num_points)

    with progress:
        # Crop to the ROI from which the COR/tilt are calculated
        progress.update(msg="Crop to ROI")

        if projections is None:
            projections = np.arange(0, stack.shape[0], dtype=int)
        LOG.debug('Projection indices: {}'.format(list(projections)))

        LOG.debug('Slices: {}'.format(model.slices))

        cropped_data = stack[list(projections), :, :][:, list(model.slices), :][:, :, roi[0]:roi[2]]
        LOG.debug("Cropped data shape: {}".format(cropped_data.shape))

        if np.any([v == 0 for v in cropped_data.shape]):
            raise ValueError('At least one axis has zero length, this ' 'will produce no usable results')

        # Obtain COR for each desired slice of ROI
        cors = pu.create_shared_array((len(model.slices), ), np.int32)
        np.copyto(cors, np.arange(len(model.slices), dtype=int))

        f = psm.create_partial(find_cor_at_slice, fwd_func=psm.return_fwd_func, sample_data=cropped_data)

        progress.update(msg="Rotation centre finding")
        psm.execute(cors, f, cores=cores, progress=progress)
        LOG.debug('CORs: {}'.format(cors))

        # Correct for left hand ROI bound
        cors += roi[0]

        # Populate results in model
        for idx, cor in enumerate(cors):
            model.set_point(idx, cor=cor)


def generate_cors(cor, gradient, num_images):
    return (np.arange(0, num_images, 1) * gradient) + cor
