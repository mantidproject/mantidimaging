# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Callable, Any, TYPE_CHECKING

from mantidimaging.core.parallel import utility as pu

if TYPE_CHECKING:
    from numpy import ndarray


def inplace3(func, data: list[pu.SharedArray] | list[pu.SharedArrayProxy], i, **kwargs):
    func(data[0].array[i], data[1].array[i], data[2].array, **kwargs)


def inplace2(func, data: list[pu.SharedArray] | list[pu.SharedArrayProxy], i, **kwargs):
    func(data[0].array[i], data[1].array[i], **kwargs)


def inplace1(func, data: list[pu.SharedArray] | list[pu.SharedArrayProxy], i, **kwargs):
    func(data[0].array[i], **kwargs)


def return_to_self(func, data: list[pu.SharedArray] | list[pu.SharedArrayProxy], i, **kwargs):
    data[0].array[i] = func(data[0].array[i], **kwargs)


def inplace_second_2d(func, data: list[pu.SharedArray] | list[pu.SharedArrayProxy], i, **kwargs):
    func(data[0].array[i], data[1].array, **kwargs)


def return_to_second_at_i(func, data: list[pu.SharedArray] | list[pu.SharedArrayProxy], i, **kwargs):
    data[1].array[i] = func(data[0].array[i], **kwargs)


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


def execute(partial_func: partial,
            arrays: list[pu.SharedArray],
            num_operations: int,
            progress=None,
            msg: str = '') -> None:
    """
    Executes a function a given number of times using the provided list of SharedArray objects.

    If all the arrays in the list use shared memory then the execution is done in parallel, with each process
    accessing the data in shared memory.
    If any arrays in the list do not use shared memory then the execution will be performed synchronously.

    :param partial_func: A function constructed using create_partial
    :param arrays: The list of SharedArray objects that the operations should be performed on
    :param num_operations: The expected number of operations - should match the number of images being processed
                           Also used to set the number of progress steps
    :param progress: Progress instance to use for progress reporting (optional)
    :param msg: Message to be shown on the progress bar
    :return:
    """

    all_data_in_shared_memory, data = _check_shared_mem_and_get_data(arrays)
    partial_func = partial(partial_func, data)
    pu.execute_impl(num_operations, partial_func, all_data_in_shared_memory, progress, msg)


ComputeFuncType = (Callable[[int, list['ndarray'], dict[str, Any]], None]
                   | Callable[[int, 'ndarray', dict[str, Any]], None])


class _Worker:

    def __init__(self, func: ComputeFuncType, arrays: list[pu.SharedArray] | list[pu.SharedArrayProxy],
                 params: dict[str, Any]):
        self.func = func
        self.arrays = arrays
        self.params = params

    def __call__(self, index: int):
        ndarrays = [sa.array for sa in self.arrays]
        if len(ndarrays) == 1:
            ndarrays = ndarrays[0]  # type: ignore[assignment]
        self.func(index, ndarrays, self.params)  # type: ignore[arg-type]


def run_compute_func(func: ComputeFuncType,
                     num_operations: int,
                     arrays: list[pu.SharedArray] | pu.SharedArray,
                     params: dict[str, Any],
                     progress=None):
    if isinstance(arrays, pu.SharedArray):
        arrays = [arrays]
    all_data_in_shared_memory, data = _check_shared_mem_and_get_data(arrays)
    worker_func = _Worker(func, data, params)
    pu.run_compute_func_impl(worker_func, num_operations, all_data_in_shared_memory, progress)


def _check_shared_mem_and_get_data(
        arrays: list[pu.SharedArray]) -> tuple[bool, list[pu.SharedArray] | list[pu.SharedArrayProxy]]:
    """
    Checks if all shared arrays in shared_list are using shared memory and returns this result in the first element
    of the tuple. The second element of the tuple gives the data to use in the processing.
    """
    data = []
    for shared_array in arrays:
        if shared_array.has_shared_memory:
            # If we're using shared memory then we must use the SharedArrayProxy for the data. This allows us to
            # look up the SharedArray from within a subprocess without needing to pass it in directly
            data.append(shared_array.array_proxy)
        else:
            return False, arrays
    return True, data
