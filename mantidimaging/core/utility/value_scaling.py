import numpy as np

from mantidimaging.core.parallel import two_shared_mem as ptsm, utility as pu
from mantidimaging.core.utility.progress_reporting import Progress

SCALE_FACTOR_ARRAY_NAME = "scale-factors-name"


def _calc_avg(data, roi_sums, roi_top=None, roi_left=None, roi_right=None, roi_bottom=None):
    return data[roi_top:roi_bottom, roi_left:roi_right].mean()


def create_factors(data: np.ndarray, roi=None, cores=None, chunksize=None, progress=None):
    """
    Calculate the scale factors as the mean of the ROI
    :param data: The data stack from which the scale factors will be calculated
    :param roi: Region of interest for which the scale factors will be calculated
    :param cores: Number of cores that will perform the calculation
    :param chunksize: How many chunks of work each core will receive
    :return: The scale factor for each image.
    """

    progress = Progress.ensure_instance(progress, num_steps=data.shape[0])
    with progress:
        img_num = data.shape[0]
        # make sure to clean up if for some reason the scale factor array still exists
        with pu.temp_shared_array((img_num,1,1)) as scale_factors:
            # turn into a 1D array, from the 3D that is returned
            scale_factors = scale_factors.reshape(img_num)

            # calculate the scale factor from original image
            calc_sums_partial = ptsm.create_partial(_calc_avg,
                                                    fwd_function=ptsm.return_to_second,
                                                    roi_left=roi[0] if roi else 0,
                                                    roi_top=roi[1] if roi else 0,
                                                    roi_right=roi[2] if roi else data[0].shape[1] - 1,
                                                    roi_bottom=roi[3] if roi else data[0].shape[0] - 1)

            data, scale_factors = ptsm.execute(data, scale_factors, calc_sums_partial, cores, chunksize,
                                               "Calculating scale factor")

        return scale_factors


def _scale_inplace(data, scale):
    np.multiply(data, scale, out=data[:])


def apply_factor(data: np.ndarray, scale_factors, cores=None, chunksize=None, progress=None):
    """
    This will apply the scale factors to the data stack.

    :param data: the data stack to which the scale factors will be applied.
    :param scale_factors: The scale factors to be applied
    """
    # scale up the data
    progress = Progress.ensure_instance(progress, num_steps=data.shape[0])
    with progress:
        scale_up_partial = ptsm.create_partial(_scale_inplace, fwd_function=ptsm.inplace_second_2d)

        # scale up all images by the mean sum of all of them, this will keep the
        # contrast the same as from the region of interest
        data, scale_factors = ptsm.execute(data, [scale_factors.mean()], scale_up_partial, cores, chunksize,
                                           "Applying scale factor", progress)

    return data
