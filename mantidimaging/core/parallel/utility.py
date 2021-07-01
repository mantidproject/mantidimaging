# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import ctypes
import multiprocessing
import os
from functools import partial
from logging import getLogger
from multiprocessing import Array
from multiprocessing.pool import Pool
from typing import List, Tuple, Type, Union, TYPE_CHECKING

import numpy as np
if TYPE_CHECKING:
    import numpy.typing as npt

from mantidimaging.core.utility.memory_usage import system_free_memory
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.size_calculator import full_size_KB

LOG = getLogger(__name__)

SimpleCType = Union[Type[ctypes.c_uint8], Type[ctypes.c_uint16], Type[ctypes.c_int32], Type[ctypes.c_int64],
                    Type[ctypes.c_float], Type[ctypes.c_double]]


def enough_memory(shape, dtype):
    return full_size_KB(shape=shape, axis=0, dtype=dtype) < system_free_memory().kb()


def create_array(shape: Tuple[int, ...], dtype: 'npt.DTypeLike' = np.float32) -> np.ndarray:
    """
    Create an array, either in a memory file (if name provided), or purely in memory (if name is None)

    :param shape: Shape of the array
    :param dtype: Dtype of the array
    :param name: Name of the shared memory array. If None, a non-shared array will be created
    :param random_name: Whether to randomise the name. Will discard anything in the `name` parameter
    :return: The created Numpy array
    """
    if not enough_memory(shape, dtype):
        raise RuntimeError(
            "The machine does not have enough physical memory available to allocate space for this data.")

    return _create_shared_array(shape, dtype)


def _create_shared_array(shape, dtype: 'npt.DTypeLike' = np.float32) -> np.ndarray:
    ctype: SimpleCType = ctypes.c_float  # default to numpy float32 / C type float
    if dtype == np.uint8 or dtype == 'uint8':
        ctype = ctypes.c_uint8
        dtype = np.uint8
    elif dtype == np.uint16 or dtype == 'uint16':
        ctype = ctypes.c_uint16
        dtype = np.uint16
    elif dtype == np.int32 or dtype == 'int32':
        ctype = ctypes.c_int32
        dtype = np.int32
    elif dtype == np.int64 or dtype == 'int64':
        ctype = ctypes.c_int64
        dtype = np.int64
    elif dtype == np.float32 or dtype == 'float32':
        ctype = ctypes.c_float
        dtype = np.float32
    elif dtype == np.float64 or dtype == 'float64':
        ctype = ctypes.c_double
        dtype = np.float64

    length = 1
    for axis_length in shape:
        length *= axis_length

    size = ctypes.sizeof(ctype(1)) * length

    LOG.info('Requested shared array with shape={}, length={}, size={}, ' 'dtype={}'.format(shape, length, size, dtype))

    array = Array(ctype, length)
    data = np.frombuffer(array.get_obj(), dtype=dtype)

    return data.reshape(shape)


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
        LOG.info("1 core specified. Running synchronously on 1 core")
        return False
    elif isinstance(shape, int):
        if shape <= 10:
            LOG.info("Shape under 10. Running synchronously on 1 core")
            return False
    elif isinstance(shape, tuple) or isinstance(shape, list):
        if shape[0] <= 10:
            LOG.info("3D axis 0 shape under 10. Running synchronously on 1 core")
            return False

    LOG.info(f"Running async on {cores} cores")
    return True


def execute_impl(img_num: int, partial_func: partial, cores: int, chunksize: int, progress: Progress, msg: str):
    task_name = f"{msg} {cores}c {chunksize}chs"
    progress = Progress.ensure_instance(progress, num_steps=img_num, task_name=task_name)
    indices_list = range(img_num)
    if multiprocessing_necessary(img_num, cores):
        with Pool(cores) as pool:
            for _ in pool.imap(partial_func, indices_list, chunksize=chunksize):
                progress.update(1, msg)
    else:
        for ind in indices_list:
            partial_func(ind)
            progress.update(1, msg)
    progress.mark_complete()
