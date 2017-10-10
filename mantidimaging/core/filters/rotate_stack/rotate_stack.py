from __future__ import (absolute_import, division, print_function)

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress


def _cli_register(parser):
    parser.add_argument(
        "-r",
        "--rotation",
        required=False,
        type=int,
        help="Rotate images by 90 degrees a number of times.\n"
        "The rotation is clockwise unless a negative number is given "
        "which indicates rotation counterclockwise.")

    return parser


def _rotate_image_inplace(data, rotation=None):
    data[:, :] = np.rot90(data[:, :], rotation)


def _rotate_image(data, rotation=None):
    return np.rot90(data[:, :], rotation)


def execute(data, rotation, flat=None, dark=None, cores=None, chunksize=None,
            progress=None):
    """
    Rotates a stack (sample, flat and dark images).

    This function only works with square images.

    If the picture is cropped first, the ROI coordinates have to be adjusted
    separately to be pointing at the NON ROTATED image!

    :param data: stack of sample images
    :param rotation: The rotation to be performed
    :param flat: flat images average
    :param dark: dark images average
    :param cores: cores for parallel execution
    :param chunksize: chunk for each worker

    :return: rotated images
    """
    h.check_data_stack(data)

    if rotation:
        # rot90 rotates counterclockwise; config.args.rotation rotates
        # clockwise
        clockwise_rotations = 4 - rotation

        if pu.multiprocessing_available():
            _execute_par(data, clockwise_rotations, cores, chunksize)
        else:
            _execute_seq(data, clockwise_rotations)

        if flat is not None:
            flat = _rotate_image(flat, clockwise_rotations, progress)
        if dark is not None:
            dark = _rotate_image(dark, clockwise_rotations, progress)

    h.check_data_stack(data)

    if flat is None and dark is None:
        return data
    else:
        return data, flat, dark


def _execute_seq(data, rotation, progress=None):
    progress = Progress.ensure_instance(progress,
                                        task_name='Rotate Stack')

    with progress:
        progress.update(msg="Starting rotation step ({0} degrees clockwise), "
                            "data type: {1}...".format(
                                rotation * 90, data.dtype))

        img_count = data.shape[0]
        progress.add_estimated_steps(img_count)
        for idx in range(0, img_count):
            data[idx] = _rotate_image(data[idx], rotation)
            progress.update()

    return data


def _execute_par(data, rotation, cores=None, chunksize=None, progress=None):
    progress = Progress.ensure_instance(progress,
                                        task_name='Rotate Stack')

    with progress:
        progress.update(msg="Starting PARALLEL rotation step ({0} degrees "
                            "clockwise), data type: {1}...".format(
                                rotation * 90, data.dtype))

        f = psm.create_partial(
            _rotate_image_inplace, fwd_func=psm.inplace, rotation=rotation)

        data = psm.execute(
            data, f, cores=cores, chunksize=chunksize, name="Rotation")

    return data
