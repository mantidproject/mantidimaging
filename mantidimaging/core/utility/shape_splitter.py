# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from logging import getLogger

import numpy as np

from mantidimaging.core.utility import size_calculator


def _calculate_ratio(current_size, max_memory, reconstruction):
    """
    Calculates the ratio of the current size to the maximum allowed memory.

    :param current_size: The size in megabytes
    :param max_memory: The maximum allowed memory

    :returns: The calculated ratio
    """

    # we are using sinograms, so the reconstructed shape will be exactly the
    # same, thus we double the size of the reconstruction
    if not reconstruction:
        ratio = current_size / max_memory
    else:
        ratio = current_size * 2 / max_memory
    return ratio


def execute(shape, axis, dtype, max_memory, max_ratio=1, reconstruction=True):
    """
    Calculate the necessary split to fit into the maximum allowed memory.

    :param shape: The shape of the data

    :param axis: The axis on which we are traversing

    :param dtype: The data type

    :param max_memory: The maximum allowed memory usage

    :param max_ratio: The maximum allowed ratio of data size per split to the
                      max_memory

    :param reconstruction: Account for reconstruction data (double the usage)
                           or not

    :returns: Tuple containing list of split indices and step.
              - split: List of start and end indices.
                       This should be traversed two elements at a time.
              - step: The step between each index in the split list.
    """
    assert axis < len(shape), "The required axis is outside the shape of the data!"

    # length will be the shape across the axis we're traversing
    length = shape[axis]

    # decorate the functions to avoid repeating parameters
    calculate_full_size = partial(size_calculator.full_size_MB, axis=axis, dtype=dtype)

    calculate_ratio = partial(_calculate_ratio, max_memory=max_memory, reconstruction=reconstruction)

    full_size = calculate_full_size(shape)

    # get the first ratio to be a whole number
    number_of_indice_splits = int(np.ceil(calculate_ratio(full_size)))

    # if number_of_indice_splits is == 1 then numpy linspace returns just [0.]
    # and a step of NaN
    if number_of_indice_splits <= 1:
        number_of_indice_splits += 1

    split, step = np.linspace(0, length, number_of_indice_splits, dtype=np.int32, retstep=True)

    # build the new shape around the axis we're traversing
    # if we're traversing along axis 0, with a shape (15,300,400)
    # this will create the new shape (step, 300, 400). If we're
    # traversing along axis 1, then it will be (15, step, 400)
    new_shape = shape[:axis] + \
        (int(step),) + shape[axis + 1:]

    while calculate_ratio(calculate_full_size(new_shape)) > max_ratio:
        getLogger(__name__).info(calculate_ratio(calculate_full_size(new_shape)))

        split, step = np.linspace(0, length, number_of_indice_splits, dtype=np.int32, retstep=True)

        new_shape = shape[:axis] + (int(step), ) + shape[axis + 1:]

        # we increase the number_of_indice_splits until we get a ratio that is
        # acceptable this means we split the data in 2, 3, 4 runs
        number_of_indice_splits += 1

    getLogger(__name__).info("Data step: {0}, with a ratio to memory: {1}, indices: {2}".format(
        step, calculate_ratio(calculate_full_size(new_shape)), split))

    return split, step
