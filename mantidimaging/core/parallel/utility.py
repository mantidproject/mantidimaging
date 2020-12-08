# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import ctypes
import os
import uuid
from contextlib import contextmanager
from functools import partial
from logging import getLogger
from multiprocessing.pool import Pool
# for some reason mypy can't find this import, nor can IDE suggestions
from multiprocessing import heap  # type: ignore
from typing import Union, Type, Optional, Tuple

import SharedArray as sa
import numpy as np

from mantidimaging.core.utility.memory_usage import system_free_memory
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.size_calculator import full_size_KB

LOG = getLogger(__name__)

SimpleCType = Union[Type[ctypes.c_uint8], Type[ctypes.c_uint16], Type[ctypes.c_int32], Type[ctypes.c_int64],
                    Type[ctypes.c_float], Type[ctypes.c_double]]

NP_DTYPE = Type[np.single]

INSTANCE_PREFIX = str(uuid.uuid4())


def free_all_owned_by_this_instance():
    for arr in [array for array in sa.list() if array.name.decode("utf-8").startswith(INSTANCE_PREFIX)]:
        sa.delete(arr.name.decode("utf-8"))


def has_other_shared_arrays() -> bool:
    return len(sa.list()) > 0


def free_all():
    for arr in [array for array in sa.list()]:
        sa.delete(arr.name.decode("utf-8"))


def create_shared_name(file_name=None) -> str:
    return f"{INSTANCE_PREFIX}-{uuid.uuid4()}{f'-{os.path.basename(file_name)}' if file_name is not None else ''}"


def delete_shared_array(name, silent_failure=True):
    try:
        LOG.debug(f"Deleting array with name: {name}")
        sa.delete(f"shm://{name}")
    except FileNotFoundError as e:
        if not silent_failure:
            raise e
        else:
            LOG.warning(f"Failed to remove SharedArray with name {name}")


def enough_memory(shape, dtype):
    return full_size_KB(shape=shape, axis=0, dtype=dtype) < system_free_memory().kb()


def allocate_output(images, shape):
    return create_array(shape, images.dtype)


def create_array(shape: Tuple[int, int, int],
                 dtype: NP_DTYPE = np.float32,
                 name: Optional[str] = None,
                 random_name=False) -> np.ndarray:
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

    if random_name:
        name = create_shared_name()

    if name is not None:
        return _create_shared_array(shape, dtype, name)
    else:
        # if the name provided is None, then a shared array, and delete the memory file
        # reference, so that when all Python references are removed the memory is
        # automatically freed
        with temp_shared_array(shape, dtype) as temp:
            return temp


def _create_shared_array(shape, dtype: Union[str, np.dtype] = np.float32, _=None):
    ctype: SimpleCType = ctypes.c_float  # default to numpy float32 / C type float
    if isinstance(dtype, np.uint8) or dtype == 'uint8':
        ctype = ctypes.c_uint8
        dtype = np.uint8
    elif isinstance(dtype, np.uint16) or dtype == 'uint16':
        ctype = ctypes.c_uint16
        dtype = np.uint16
    elif isinstance(dtype, np.int32) or dtype == 'int32':
        ctype = ctypes.c_int32
        dtype = np.int32
    elif isinstance(dtype, np.int64) or dtype == 'int64':
        ctype = ctypes.c_int64
        dtype = np.int64
    elif isinstance(dtype, np.float32) or dtype == 'float32':
        ctype = ctypes.c_float
        dtype = np.float32
    elif isinstance(dtype, np.float64) or dtype == 'float64':
        ctype = ctypes.c_double
        dtype = np.float64

    length = 1
    for axis_length in shape:
        length *= axis_length

    size = ctypes.sizeof(ctype(1)) * length

    LOG.info('Requested shared array with shape={}, length={}, size={}, ' 'dtype={}'.format(shape, length, size, dtype))

    arena = heap.Arena(size)
    mem = memoryview(arena.buffer)

    array_type = ctype * length
    array = array_type.from_buffer(mem)

    data = np.frombuffer(array, dtype=dtype)

    return data.reshape(shape)


# def _create_shared_array(shape: Tuple[int, int, int], dtype: NP_DTYPE, name: str) -> np.ndarray:
#     """
#     :param dtype:
#     :param shape:
#     :param name: Name used for the shared memory file by which this memory chunk will be identified
#     """
#     LOG.info(f"Requested shared array with name='{name}', shape={shape}, dtype={dtype}")
#     memory_file_name = f"shm://{name}"
#     arr = sa.create(memory_file_name, shape, dtype)
#     return arr


@contextmanager
def temp_shared_array(shape, dtype: NP_DTYPE = np.float32, force_name=None) -> np.ndarray:
    temp_name = create_shared_name() if not force_name else force_name
    array = _create_shared_array(shape, dtype, temp_name)
    try:
        yield array
    finally:
        delete_shared_array(temp_name)


def multiprocessing_available():
    try:
        # ignore error about unused import
        import multiprocessing  # noqa: F401
        return multiprocessing
    except ImportError:
        return False


def get_cores():
    mp = multiprocessing_available()
    # get max cores on the system as default
    if not mp:
        return 1
    else:
        return mp.cpu_count()


def generate_indices(num_images):
    """
    Generate indices for each image.

    :param num_images: The number of images.
    """
    return range(num_images)


def calculate_chunksize(cores):
    # TODO possible proper calculation of chunksize, although best performance
    # has been with 1
    return 1


def multiprocessing_necessary(shape: Union[int, Tuple[int, int, int]], cores) -> bool:
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
    indices_list = generate_indices(img_num)
    if multiprocessing_necessary(img_num, cores):
        with Pool(cores) as pool:
            for _ in pool.imap(partial_func, indices_list, chunksize=chunksize):
                progress.update(1, msg)
    else:
        for ind in indices_list:
            partial_func(ind)
            progress.update(1, msg)
    progress.mark_complete()
