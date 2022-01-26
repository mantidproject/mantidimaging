# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from typing import List

import numpy

from mantidimaging.core.parallel import utility as pu

shared_list: List[numpy.ndarray] = []


def inplace3(func, i, **kwargs):
    global shared_list
    func(shared_list[0][i], shared_list[1][i], shared_list[2], **kwargs)


def inplace2(func, i, **kwargs):
    global shared_list
    func(shared_list[0][i], shared_list[1][i], **kwargs)


def inplace1(func, i, **kwargs):
    global shared_list
    func(shared_list[0][i], **kwargs)


def return_to_self(func, i, **kwargs):
    global shared_list
    shared_list[0][i] = func(shared_list[0][i], **kwargs)


def inplace_second_2d(func, i, **kwargs):
    global shared_list
    func(shared_list[0][i], shared_list[1], **kwargs)


def return_to_second(func, i, **kwargs):
    global shared_list
    shared_list[1] = func(shared_list[0][i], **kwargs)


def return_to_second_at_i(func, i, **kwargs):
    global shared_list
    shared_list[1][i] = func(shared_list[0][i], **kwargs)


def arithmetic(func, i):
    global shared_list
    func(shared_list[0][i], *shared_list[1:])


def create_partial(func, fwd_function, **kwargs):
    """
    Create a partial using functools.partial, to forward the kwargs to the
    parallel execution of imap.

    If you seem to be getting nans, check if the correct fwd_function is set!

    :param func: Function that will be executed
    :param fwd_function: The function will be forwarded through function.
    :param kwargs: kwargs to forward to the function func that will be executed
    :return: The decorated forwarded function, ready for further execution
    """
    return partial(fwd_function, func, **kwargs)


def execute(partial_func: partial, num_operations: int, progress=None, msg: str = '', cores=None) -> None:
    """
    Executes a function in parallel with shared memory between the processes.

    The array must have been created using
    parallel.utility.create_shared_array(shape, dtype).

    If the input array IS NOT a shared array, the data will NOT BE CHANGED!

    The reason for that is that the processes don't work on the data, but on a
    copy.

    When they process it and return the result, THE RESULT IS NOT ASSIGNED BACK
    TO REPLACE THE ORIGINAL, it is discarded.

    - imap_unordered gives the images back in random order
    - map and map_async do not improve speed performance
    - imap seems to be the best choice

    Using _ in the for _ enumerate is slightly faster, because the tuple
    from enumerate isn't unpacked, and thus some time is saved.

    From performance tests, the chunksize doesn't seem to make much of a
    difference, but having larger chunks usually led to slower performance:

    Shape: (50,512,512)
    1 chunk 3.06s
    2 chunks 3.05s
    3 chunks 3.07s
    4 chunks 3.06s
    5 chunks 3.16s
    6 chunks 3.06s
    7 chunks 3.058s
    8 chunks 3.25s
    9 chunks 3.45s

    :param partial_func: A function constructed using create_partial
    :param num_operations: The expected number of operations - should match the number of images being processed
                           Also used to set the number of progress steps
    :param cores: number of cores that the processing will use
    :param progress: Progress instance to use for progress reporting (optional)
    :param msg: Message to be shown on the progress bar
    :return:
    """

    if not cores:
        cores = pu.get_cores()

    chunksize = pu.calculate_chunksize(cores)

    pu.execute_impl(num_operations, partial_func, cores, chunksize, progress, msg)

    global shared_list
    shared_list = []
