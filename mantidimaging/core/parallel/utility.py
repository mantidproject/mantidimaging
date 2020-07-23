import atexit
import ctypes
import os
import uuid
from contextlib import contextmanager
from logging import getLogger
from multiprocessing.pool import Pool
from typing import Union, Type, Optional, Tuple

import SharedArray as sa
import numpy as np

from mantidimaging.core.utility.progress_reporting import Progress

LOG = getLogger(__name__)

SimpleCType = Union[Type[ctypes.c_uint8], Type[ctypes.c_uint16], Type[ctypes.c_int32], Type[ctypes.c_int64],
                    Type[ctypes.c_float], Type[ctypes.c_double]]


def free_all():
    for arr in sa.list():
        sa.delete(arr.name.decode("utf-8"))


atexit.register(free_all)

NP_DTYPE = Type[np.single]


def create_shared_name(file_name=None) -> str:
    return f"{uuid.uuid4()}{f'-{os.path.basename(file_name)}' if file_name is not None else ''}"


def delete_shared_array(name, silent_failure=False):
    try:
        sa.delete(f"shm://{name}")
    except FileNotFoundError as e:
        if not silent_failure:
            raise e


def create_array(shape: Tuple[int, int, int], dtype: NP_DTYPE = np.float32,
                 name: Optional[str] = None) -> np.ndarray:
    """
    Create an array, either in a memory file (if name provided), or purely in memory (if name is None)

    :param name: Name of the shared memory array. If None, a non-shared array will be created
    :param shape: Shape of the array
    :param dtype: Dtype of the array
    :return: The created Numpy array
    """
    if name is not None:
        return _create_shared_array(shape, dtype, name)
    else:
        # if the name provided is None, then allocate an array only visible to this process
        return np.zeros(shape, dtype)


def _create_shared_array(shape: Tuple[int, int, int], dtype: NP_DTYPE, name: str) -> np.ndarray:
    """
    :param dtype:
    :param shape:
    :param name: Name used for the shared memory file by which this memory chunk will be identified
    """
    LOG.info(f"Requested shared array with name='{name}', shape={shape}, dtype={dtype}")
    memory_file_name = f"shm://{name}"
    arr = sa.create(memory_file_name, shape, dtype)
    return arr


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


def multiprocessing_necessary(shape, cores) -> bool:
    # This environment variable will be present when running PYDEVD from PyCharm
    # and that has the bug that multiprocessing Pools can never finish `.join()` ing
    # thus never actually finish their processing.
    if 'PYDEVD_LOAD_VALUES_ASYNC' in os.environ:
        LOG.info("Debugging environment variable 'PYDEVD_LOAD_VALUES_ASYNC' found. Running synchronously on 1 core")
        return False
    if cores == 1 or shape[0] < 10:
        return False
    return True


def execute_impl(img_num, partial_func, cores, chunksize, name, progress, msg):
    task_name = name + " " + str(cores) + "c " + str(chunksize) + "chs"
    progress = Progress.ensure_instance(progress, num_steps=img_num, task_name=task_name)
    indices_list = generate_indices(img_num)
    if cores > 1:
        with Pool(cores) as pool:
            for _ in pool.imap(partial_func, indices_list, chunksize=chunksize):
                progress.update(1, msg)
    else:
        for ind in indices_list:
            partial_func(ind)
            progress.update(1, msg)
    progress.mark_complete()
