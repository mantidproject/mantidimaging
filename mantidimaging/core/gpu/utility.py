import numpy as np

MAX_CUPY_MEMORY = 0.8
FREE_MEMORY_FACTOR = 0.8

try:
    import cupy as cp

    mempool = cp.get_default_memory_pool()

    CUPY_INSTALLED = True
except ImportError:
    CUPY_INSTALLED = False


def gpu_available():
    return CUPY_INSTALLED


def allocate_gpu_memory():
    with cp.cuda.Device(0):
        mempool.set_limit(fraction=MAX_CUPY_MEMORY)


def _create_pinned_memory(cpu_array):
    """
    Use pinned memory in order to store a numpy array on the GPU.
    :param cpu_array: The numpy array.
    :return: src
    """
    mem = cp.cuda.alloc_pinned_memory(cpu_array.nbytes)
    src = np.frombuffer(mem, cpu_array.dtype, cpu_array.size).reshape(cpu_array.shape)
    src[...] = cpu_array
    return src


def get_free_bytes():
    free_bytes = mempool.free_bytes()
    if free_bytes > 0:
        return free_bytes * FREE_MEMORY_FACTOR
    return mempool.get_limit() * FREE_MEMORY_FACTOR
