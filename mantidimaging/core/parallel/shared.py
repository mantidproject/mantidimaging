# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from typing import List, Tuple

from mantidimaging.core.parallel import utility as pu

shared_list: List[pu.SharedArray] = []


def inplace3(func, array_details, i, **kwargs):
    data = _get_array_list(array_details)
    func(data[0].array[i], data[1].array[i], data[2].array, **kwargs)


def inplace2(func, array_details, i, **kwargs):
    data = _get_array_list(array_details)
    func(data[0].array[i], data[1].array[i], **kwargs)


def inplace1(func, array_details, i, **kwargs):
    data = _get_array_list(array_details)
    func(data[0].array[i], **kwargs)


def return_to_self(func, array_details, i, **kwargs):
    data = _get_array_list(array_details)
    data[0].array[i] = func(data[0].array[i], **kwargs)


def inplace_second_2d(func, array_details, i, **kwargs):
    data = _get_array_list(array_details)
    func(data[0].array[i], data[1].array, **kwargs)


def return_to_second_at_i(func, array_details, i, **kwargs):
    data = _get_array_list(array_details)
    data[1].array[i] = func(data[0].array[i], **kwargs)


def arithmetic(func, array_details, i, arg_list):
    data = _get_array_list(array_details)
    func(data[0].array[i], *arg_list)


def _get_array_list(array_details):
    if not array_details:
        return shared_list
    else:
        return pu.lookup_shared_arrays(array_details)


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

    all_data_in_shared_memory, shared_array_details = _check_shared_mem_details()

    if not all_data_in_shared_memory:
        cores = 1
    elif not cores:
        cores = pu.get_cores()

    partial_func = partial(partial_func, shared_array_details)

    chunksize = pu.calculate_chunksize(cores)

    pu.execute_impl(num_operations, partial_func, cores, chunksize, progress, msg)

    global shared_list
    shared_list = []


def _check_shared_mem_details() -> Tuple[bool, List[pu.SharedArrayDetails]]:
    """
    Checks if all shared arrays in shared_list are using shared memory and returns this result in the first element
    of the tuple. If all the arrays are using shared memory, then the list of SharedArrayDetails are returned in the
    second element of the tuple.
    """
    details = []
    for shared_array in shared_list:
        if shared_array.has_shared_memory:
            details.append(shared_array.details)
        else:
            return False, []
    return True, details
