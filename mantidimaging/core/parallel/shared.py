# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Any, TYPE_CHECKING
from collections.abc import Callable

from mantidimaging.core.parallel import utility as pu

if TYPE_CHECKING:
    from numpy import ndarray

ComputeFuncType = (Callable[[int, list['ndarray'], dict[str, Any]], None]
                   | Callable[[int, 'ndarray', dict[str, Any]], None])


class _Worker:
    """
    Workers only attach to existing SharedMemory via SharedArrayProxy/SharedArray
    They never create or free SharedArrays, and only access contiguous slices
    This avoids the premature unlinks when
    ImageStack creates many temporary SharedArrays.
    """

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
                     progress=None) -> None:
    """
    SharedArray works safely here because operations use a single, pre-allocated
    shared buffer with a fixed lifetime. No slicing, reassignment, or temporary
    SharedArrays are created, and workers only attach to the existing buffer.
    This controlled pattern avoids the premature unlinks and writes that
    occur in ImageStack.
    """
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
