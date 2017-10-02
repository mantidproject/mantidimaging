from __future__ import (absolute_import, division, print_function)

import scipy.misc

from mantidimaging import helper as h
from mantidimaging.core.parallel import exclusive_mem as pem
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress


def _cli_register(parser):
    parser.add_argument(
        "--rebin",
        required=False,
        type=float,
        help="Rebin factor by which the images will be rebinned. "
        "This could be any positive float number.\n"
        "If not specified no scaling will be done.")

    parser.add_argument(
        "--rebin-mode",
        required=False,
        type=str,
        default=modes()[0],
        choices=modes(),
        help="Default: %(default)s\n"
        "Specify which interpolation mode will be used for the scaling of the "
        "image.")

    return parser


def modes():
    return ['nearest', 'lanczos', 'bilinear', 'bicubic', 'cubic']


def execute(data, rebin_param, mode, cores=None, chunksize=None,
            progress=None):
    """
    :param data: Sample data which is to be processed. Expected in radiograms

    :param rebin_param: int, float or tuple
                        int - Percentage of current size.
                        float - Fraction of current size.
                        tuple - Size of the output image (x, y).

    :param mode: Interpolation to use for re-sizing
                 ('nearest', 'lanczos', 'bilinear', 'bicubic' or 'cubic').

    :param cores: The number of cores that will be used to process the data.

    :param chunksize: The number of chunks that each worker will receive.

    :return: The processed 3D numpy.ndarray
    """
    h.check_data_stack(data)

    param_valid = False
    if rebin_param is None:
        pass
    elif isinstance(rebin_param, tuple):
        param_valid = rebin_param[0] > 0 and rebin_param[1] > 0
    else:
        param_valid = rebin_param > 0

    if param_valid:
        if pu.multiprocessing_available():
            data = _execute_par(data, rebin_param, mode, cores, chunksize,
                                progress)
        else:
            data = _execute_seq(data, rebin_param, mode, progress)

    return data


def _execute_par(data, rebin_param, mode, cores=None, chunksize=None,
                 progress=None):
    progress = Progress.ensure_instance(progress,
                                        task_name='Rebin')

    resized_data = _create_reshaped_array(data.shape, rebin_param)

    with progress:
        progress.update(msg="Starting PARALLEL image rebinning.")

        f = pem.create_partial(
                scipy.misc.imresize, size=rebin_param, interp=mode)

        resized_data = pem.execute(
            data, f, cores, chunksize, "Rebinning", output_data=resized_data)

    return resized_data


def _execute_seq(data, rebin_param, mode, progress=None):
    progress = Progress.ensure_instance(progress,
                                        task_name='Rebin')

    with progress:
        progress.update(msg="Starting image rebinning.")

        resized_data = _create_reshaped_array(data.shape, rebin_param)

        num_images = resized_data.shape[0]
        progress.add_estimated_steps(num_images)

        for idx in range(num_images):
            resized_data[idx] = scipy.misc.imresize(
                data[idx], rebin_param, interp=mode)
            progress.update()

    return resized_data


def _create_reshaped_array(old_shape, rebin_param):
    num_images = old_shape[0]

    # use SciPy's calculation to find the expected dimensions
    # int to avoid visible deprecation warning
    if isinstance(rebin_param, tuple):
        expected_dimy = int(rebin_param[0])
        expected_dimx = int(rebin_param[1])
    else:
        expected_dimy = int(rebin_param * old_shape[1])
        expected_dimx = int(rebin_param * old_shape[2])

    # allocate memory for images with new dimensions
    return pu.create_shared_array((num_images, expected_dimy, expected_dimx))
