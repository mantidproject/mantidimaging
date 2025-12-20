# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
from logging import getLogger
from multiprocessing import shared_memory
from typing import TYPE_CHECKING
from collections.abc import Callable

import numpy as np

from mantidimaging.core.utility.memory_usage import system_free_memory
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.size_calculator import full_size_KB, full_size_bytes
from mantidimaging.core.parallel import manager as pm

if TYPE_CHECKING:
    from functools import partial
    import numpy.typing as npt
    from multiprocessing.shared_memory import SharedMemory

LOG = getLogger(__name__)


def enough_memory(shape, dtype) -> bool:
    return full_size_KB(shape=shape, dtype=dtype) < system_free_memory().kb()


def create_array(shape: tuple[int, ...], dtype: npt.DTypeLike = np.float32) -> SharedArray:
    """
    Create an array in shared memory

    :param shape: Shape of the array
    :param dtype: Dtype of the array
    :return: The created SharedArray
    """
    if not enough_memory(shape, dtype):
        raise RuntimeError(
            "The machine does not have enough physical memory available to allocate space for this data.")

    return _create_shared_array(shape, dtype)


def _create_shared_array(shape: tuple[int, ...], dtype: npt.DTypeLike = np.float32) -> SharedArray:
    # No alignment checks. Some dtypes require specific alignment, raw SharedMemory does not ensure it.
    size = full_size_bytes(shape, dtype)
    name = pm.generate_mi_shared_mem_name()
    mem = shared_memory.SharedMemory(name=name, create=True, size=size)
    return _read_array_from_shared_memory(shape, dtype, mem, True)


def _read_array_from_shared_memory(shape: tuple[int, ...], dtype: npt.DTypeLike, mem: SharedMemory,
                                   free_mem_on_delete: bool) -> SharedArray:
    array: np.ndarray = np.ndarray(shape, dtype=dtype, buffer=mem.buf)
    return SharedArray(array, mem, free_mem_on_del=free_mem_on_delete)


def copy_into_shared_memory(array: np.ndarray) -> SharedArray:
    # writes arrays unsafely assumes array is contiguous.
    # corrupted shared memory → workers crash → numpy crashes → OS access violation.
    shared_array = create_array(array.shape, array.dtype)
    shared_array.array[:] = array[:]
    return shared_array


def calculate_chunksize(cores):
    """
    TODO possible proper calculation of chunksize, although best performance has been with 1
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
    """
    return 1


def multiprocessing_necessary(shape: int, is_shared_data: bool) -> bool:
    # This environment variable will be present when running PYDEVD from PyCharm
    # and that has the bug that multiprocessing Pools can never finish `.join()` ing
    # thus never actually finish their processing.
    if 'PYDEVD_LOAD_VALUES_ASYNC' in os.environ and 'PYTEST_CURRENT_TEST' not in os.environ:
        LOG.info("Debugging environment variable 'PYDEVD_LOAD_VALUES_ASYNC' found. Running synchronously on 1 core")
        return False

    if not is_shared_data:
        LOG.info("Not all of the data uses shared memory")
        return False
    elif shape <= 10:
        LOG.info("Shape under 10")
        return False

    LOG.info("Multiprocessing required")
    return True


def execute_impl(img_num: int, partial_func: partial, is_shared_data: bool, progress: Progress, msg: str) -> None:
    task_name = f"{msg}"
    progress = Progress.ensure_instance(progress, num_steps=img_num, task_name=task_name)
    indices_list = range(img_num)
    if multiprocessing_necessary(img_num, is_shared_data) and pm.pool:
        LOG.info(f"Running async on {pm.cores} cores")
        # Using _ in the for _ enumerate is slightly faster, because the tuple from enumerate isn't unpacked,
        # and thus some time is saved
        # Using imap here seems to be the best choice:
        # - imap_unordered gives the images back in random order
        # - map and map_async do not improve speed performance
        for _ in pm.pool.imap(partial_func, indices_list, chunksize=calculate_chunksize(pm.cores)):
            progress.update(1, msg)
    else:
        LOG.info("Running synchronously on 1 core")
        for ind in indices_list:
            partial_func(ind)
            progress.update(1, msg)
    progress.mark_complete()


def run_compute_func_impl(worker_func: Callable[[int], None],
                          num_operations: int,
                          is_shared_data: bool,
                          progress=None,
                          msg: str = "") -> None:
    task_name = f"{msg}"
    progress = Progress.ensure_instance(progress, num_steps=num_operations, task_name=task_name)
    indices_list = range(num_operations)
    if multiprocessing_necessary(num_operations, is_shared_data) and pm.pool:
        LOG.info(f"Running async on {pm.cores} cores")
        for _ in pm.pool.imap(worker_func, indices_list, chunksize=calculate_chunksize(pm.cores)):
            progress.update(1, msg)
    else:
        LOG.info("Running synchronously on 1 core")
        for ind in indices_list:
            worker_func(ind)
            progress.update(1, msg)
    progress.mark_complete()


class SharedArray:

    def __init__(self, array: np.ndarray, shared_memory: SharedMemory | None, free_mem_on_del: bool = True):
        # SharedArray breaks the only safe invariant: .array must always map mem.buf
        # This overwrites the attribute instead of storing the ndarray as _array.
        self.array = array
        self._shared_memory = shared_memory
        self._free_mem_on_del = free_mem_on_del

    def __del__(self):
        # . __del__ frees SharedMemory at unpredictable times
        # __del__ frees SharedMemory nondeterministically
        # On Windows, unlink() destroys the memory block immediately.
        # Linux is lazy
        # 0xC0000005 failures.
        if self.has_shared_memory:
            self._shared_memory.close()
            if self._free_mem_on_del:
                try:
                    self._shared_memory.unlink()
                except FileNotFoundError:
                    # Do nothing, memory has already been freed
                    pass

    @property
    def has_shared_memory(self) -> bool:
        return self._shared_memory is not None

    @property
    def array_proxy(self) -> SharedArrayProxy:
        # Proxy depends on .array for shape/dtype, but .array can be
        # reassigned, so the proxy may attach with incorrect metadata.
        mem_name = self._shared_memory.name if self._shared_memory else None
        return SharedArrayProxy(mem_name=mem_name, shape=self.array.shape, dtype=self.array.dtype)


class SharedArrayProxy:

    def __init__(self, mem_name: str | None, shape: tuple[int, ...], dtype: npt.DTypeLike):
        self._mem_name = mem_name
        self._shape = shape
        self._dtype = dtype
        # Cached SharedArray may become invalid if parent frees memory early.
        self._shared_array: SharedArray | None = None

    @property
    def array(self) -> np.ndarray:
        if self._shared_array is None:
            # If another SharedArray has already unlinked memory,
            # SharedMemory(name=...) may fail or attach to invalid memory.
            mem = shared_memory.SharedMemory(name=self._mem_name)
            # _read_array_from_shared_memory trusts the caller completely
            self._shared_array = _read_array_from_shared_memory(self._shape, self._dtype, mem, False)
        # .array may have been reassigned; no guarantee this is backed by SharedMemory.
        return self._shared_array.array