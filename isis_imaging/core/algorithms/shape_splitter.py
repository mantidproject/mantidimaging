from __future__ import absolute_import, division, print_function

from functools import partial

import numpy as np

import isis_imaging.helper as h
from isis_imaging.core.algorithms import size_calculator


def _calculate_ratio(current_size, max_memory, no_reconstruction):
    """
    Calculates the ratio of the current size to the maximum allowed memory.

    :param current_size: The size in bits

    :returns: The calculated ratio
    """

    # we are using sinograms, so the reconstructed shape will be exactly the same,
    # thus we double the size of the reconstruction
    if no_reconstruction:
        ratio = current_size / max_memory
    else:
        ratio = current_size * 2 / max_memory
    return ratio


def execute(shape, axis, dtype, max_memory, max_ratio=1, no_reconstruction=False):
    """
    Calculate the necessary split to fit into the maximum allowed memory.

    :returns: Tuple containing list of split indices and step.
                - split: List of start and end indices. This should be traversed two elements at a time.
                - step: The step between each index in the split list.
    """
    assert axis < len(
        shape), "The required axis is outside the shape of the data!"

    # length will be the shape across the axis we're traversing
    length = shape[axis]

    # decorate the functions to avoid repeating parameters
    calculate_full_size = partial(
        size_calculator.full_size, axis=axis, dtype=dtype)

    calculate_ratio = partial(_calculate_ratio, max_memory=max_memory,
                              no_reconstruction=no_reconstruction)

    full_size = calculate_full_size(shape)

    # get the first ratio to be a whole number
    ratio = int(np.ceil(calculate_ratio(full_size)))
    # if ratio is == 1 then numpy linspace returns just [0.] and a step of NaN
    if ratio <= 1:
        ratio += 1

    split, step = np.linspace(
        0, length, ratio, dtype=np.int32, retstep=True)

    # build the new shape around the axis we're traversing
    # if we're traversing along axis 0, with a shape (15,300,400)
    # this will create the new shape (step, 300, 400). If we're
    # traversing along axis 1, then it will be (15, step, 400)
    new_shape = shape[:axis] + \
        (int(step),) + shape[axis + 1:]

    while calculate_ratio(calculate_full_size(new_shape)) > max_ratio:
        split, step = np.linspace(
            0, length, ratio, dtype=np.int32, retstep=True)

        new_shape = shape[:axis] + (int(step), ) + shape[axis + 1:]

    h.tomo_print_note("Step per reconstruction: {0}, with a ratio to memory: {1}, indices: {2}".format(step, calculate_ratio(
        calculate_full_size(new_shape)), split))

    return split, step
