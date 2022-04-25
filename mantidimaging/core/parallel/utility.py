# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import multiprocessing
import os
from functools import partial
from logging import getLogger
from multiprocessing import shared_memory
from multiprocessing.shared_memory import SharedMemory
from typing import List, Tuple, Union, TYPE_CHECKING, Optional

import numpy as np

if TYPE_CHECKING:
    import numpy.typing as npt

from mantidimaging.core.utility.memory_usage import system_free_memory
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.size_calculator import full_size_KB, full_size_bytes
from mantidimaging.core.parallel import manager as pm

LOG = getLogger(__name__)


def enough_memory(shape, dtype):
    return full_size_KB(shape=shape, dtype=dtype) < system_free_memory().kb()


def create_array(shape: Tuple[int, ...], dtype: 'npt.DTypeLike' = np.float32) -> 'SharedArray':
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


def _create_shared_array(shape: Tuple[int, ...], dtype: 'npt.DTypeLike' = np.float32) -> 'SharedArray':
    size = full_size_bytes(shape, dtype)

    LOG.info(f'Requested shared array with shape={shape}, size={size}, dtype={dtype}')

    name = pm.generate_mi_shared_mem_name()
    mem = shared_memory.SharedMemory(name=name, create=True, size=size)
    return _read_array_from_shared_memory(shape, dtype, mem, True)


def _read_array_from_shared_memory(shape: Tuple[int, ...], dtype: 'npt.DTypeLike', mem: SharedMemory,
                                   free_mem_on_delete: bool) -> 'SharedArray':
    array = np.ndarray(shape, dtype=dtype, buffer=mem.buf)
    return SharedArray(array, mem, free_mem_on_del=free_mem_on_delete)


def copy_into_shared_memory(array: np.ndarray) -> 'SharedArray':
    shared_array = create_array(array.shape, array.dtype)
    shared_array.array[:] = array[:]
    return shared_array


def get_cores():
    return multiprocessing.cpu_count()


def calculate_chunksize(cores):
    # TODO possible proper calculation of chunksize, although best performance
    # has been with 1
    return 1


def multiprocessing_necessary(shape: Union[int, Tuple[int, int, int], List], cores) -> bool:
    # This environment variable will be present when running PYDEVD from PyCharm
    # and that has the bug that multiprocessing Pools can never finish `.join()` ing
    # thus never actually finish their processing.
    if 'PYDEVD_LOAD_VALUES_ASYNC' in os.environ and 'PYTEST_CURRENT_TEST' not in os.environ:
        LOG.info("Debugging environment variable 'PYDEVD_LOAD_VALUES_ASYNC' found. Running synchronously on 1 core")
        return False

    if cores == 1:
        LOG.info("1 core specified")
        return False
    elif isinstance(shape, int):
        if shape <= 10:
            LOG.info("Shape under 10")
            return False
    elif isinstance(shape, tuple) or isinstance(shape, list):
        if shape[0] <= 10:
            LOG.info("3D axis 0 shape under 10")
            return False

    LOG.info("Multiprocessing required")
    return True


def execute_impl(img_num: int, partial_func: partial, cores: int, chunksize: int, progress: Progress, msg: str):
    task_name = f"{msg} {cores}c {chunksize}chs"
    progress = Progress.ensure_instance(progress, num_steps=img_num, task_name=task_name)
    indices_list = range(img_num)
    if multiprocessing_necessary(img_num, cores) and pm.pool:
        LOG.info(f"Running async on {cores} cores")
        for _ in pm.pool.imap(partial_func, indices_list, chunksize=chunksize):
            progress.update(1, msg)
    else:
        LOG.info("Running synchronously on 1 core")
        for ind in indices_list:
            partial_func(ind)
            progress.update(1, msg)
    progress.mark_complete()


class SharedArray:
    def __init__(self, array: np.ndarray, shared_memory: Optional[SharedMemory], free_mem_on_del: bool = True):
        self.array = array
        self._shared_memory = shared_memory
        self._free_mem_on_del = free_mem_on_del

    def __del__(self):
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
    def array_proxy(self) -> 'SharedArrayProxy':
        mem_name = self._shared_memory.name if self._shared_memory else None
        return SharedArrayProxy(mem_name=mem_name, shape=self.array.shape, dtype=self.array.dtype)


class SharedArrayProxy:
    def __init__(self, mem_name: Optional[str], shape: Tuple[int, ...], dtype: 'npt.DTypeLike'):
        self._mem_name = mem_name
        self._shape = shape
        self._dtype = dtype
        self._shared_array: Optional['SharedArray'] = None

    @property
    def array(self) -> np.ndarray:
        if self._shared_array is None:
            mem = shared_memory.SharedMemory(name=self._mem_name)
            self._shared_array = _read_array_from_shared_memory(self._shape, self._dtype, mem, False)
        return self._shared_array.array
