from logging import getLogger

import numpy as np

LOG = getLogger(__name__)


def create_shared_array(shape, dtype=np.float32):
    from multiprocessing import heap
    import ctypes

    ctype = ctypes.c_float  # default to numpy float32 / C type float
    if isinstance(dtype, np.uint16) or dtype == 'uint16':
        ctype = ctypes.c_int16
        dtype = np.uint16
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
