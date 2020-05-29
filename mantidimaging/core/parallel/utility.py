import ctypes
import os
from contextlib import contextmanager
from logging import getLogger
from typing import Union, Type

import SharedArray as sa
import numpy as np
import atexit


LOG = getLogger(__name__)

SimpleCType = Union[Type[ctypes.c_uint8], Type[ctypes.c_uint16], Type[ctypes.c_int32], Type[ctypes.c_int64],
                    Type[ctypes.c_float], Type[ctypes.c_double]]

def free_all():
    for arr in sa.list():
        sa.delete(arr.name.decode("utf-8"))


atexit.register(free_all)

def _format_name(name):
    return os.path.basename(name)


def delete_shared_array(name):
    sa.delete(f"shm://{_format_name(name)}")


def create_shared_array(name, shape, dtype: Union[str, np.dtype] = np.float32):
    """
    :param name: Name used for the shared memory file by which this memory chunk will be identified
    """
    formatted_name = _format_name(name)
    LOG.info(f"Requested shared array with name='{formatted_name}', shape={shape}, dtype={dtype}")
    return sa.create(f"shm://{formatted_name}", shape, dtype)

@contextmanager
def temp_shared_array(shape, dtype):
    temp_name = "temp_array"
    array = create_shared_array(temp_name, shape, dtype)
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
