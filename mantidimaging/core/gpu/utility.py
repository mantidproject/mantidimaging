import numpy as np
from typing import List

MAX_CUPY_MEMORY = 0.8
FREE_MEMORY_FACTOR = 0.8
MAX_GPU_SLICES = 100

try:
    import cupy as cp

    mempool = cp.get_default_memory_pool()

    CUPY_INSTALLED = True
except ImportError:
    CUPY_INSTALLED = False

EQUIVALENT_PAD_MODE = {
    "reflect": "symmetric",
    "constant": "constant",
    "nearest": "edge",
    "mirror": "reflect",
    "wrap": "wrap",
}


def gpu_available():
    return CUPY_INSTALLED


def _synchronise():
    cp.cuda.Stream.null.synchronize()
    cp.cuda.runtime.deviceSynchronize()


def _free_memory_pool(arrays=[]):
    """
    Delete the existing GPU arrays and free blocks.
    """
    _synchronise()
    if arrays:
        arrays.clear()
    _synchronise()
    mempool.free_all_blocks()


def _allocate_gpu_memory():
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


def _send_single_array_to_gpu(cpu_array, stream=cp.cuda.Stream(non_blocking=True)):
    pinned_memory = _create_pinned_memory(cpu_array.copy())
    gpu_array = cp.empty(pinned_memory.shape, dtype=cpu_array.dtype)
    gpu_array.set(pinned_memory, stream=stream)
    return gpu_array


def _send_arrays_to_gpu_with_pinned_memory(cpu_arrays, streams=None):
    """
    Transfer the arrays to the GPU using pinned memory. This takes either a single numpy array or a list of numpy arrays as arguments.
    """
    try:

        if not isinstance(cpu_arrays, List):
            return _send_single_array_to_gpu(cpu_arrays, streams)

        gpu_arrays = []

        for i in range(len(cpu_arrays)):
            gpu_arrays.append(_send_single_array_to_gpu(cpu_arrays[i], streams[i]))

        return gpu_arrays

    except cp.cuda.memory.OutOfMemoryError:
        print("GPU is out of memory...")
        return []


def get_free_bytes():
    free_bytes = mempool.free_bytes()
    if free_bytes > 0:
        return free_bytes * FREE_MEMORY_FACTOR
    return mempool.get_limit() * FREE_MEMORY_FACTOR


def create_dim_block_and_grid_args(data):
    """
    Create the block and grid arguments that are passed to the cupy. These determine how the array
    is broken up.
    :param data: The array that will be processed using the GPU.
    :return
    """
    N = 10
    block_size = tuple(N for _ in range(data.ndim))
    grid_size = tuple(shape // N for shape in data.shape)
    return block_size, grid_size


def _create_padded_array(data, pad_size, scipy_mode):

    pad_mode = EQUIVALENT_PAD_MODE[scipy_mode]

    if data.ndim == 2:
        return np.pad(
            data, pad_width=((pad_size, pad_size), (pad_size, pad_size)), mode=pad_mode
        )
    else:
        return np.pad(
            data,
            pad_width=((0, 0), (pad_size, pad_size), (pad_size, pad_size)),
            mode=pad_mode,
        )


def _replace_gpu_array_contents(
    gpu_array, cpu_array, stream=cp.cuda.Stream(non_blocking=True)
):
    gpu_array.set(cpu_array, stream)


def median_filter(data, size, mode, progress):

    # Synchronize and free memory before making an assessment about available space
    _free_memory_pool()

    # Compute the pad size
    pad_size = _get_padding_value(size)
    n_images = data.shape[0]

    # Set the maxim,um number of images that will be on the GPU at a time
    if n_images > MAX_GPU_SLICES:
        slice_limit = MAX_GPU_SLICES
    else:
        # If the number of images is smaller than the slice limit, use that instead
        slice_limit = n_images

    result = np.empty_like(data)

    cpu_padded_slices = [
        _create_padded_array(data_slice, pad_size) for data_slice in data
    ]
    streams = [cp.cuda.Stream(non_blocking=True) for _ in range(slice_limit)]

    gpu_data_slices = _send_arrays_to_gpu_with_pinned_memory(
        data[:slice_limit], streams
    )
    gpu_padded_data = _send_arrays_to_gpu_with_pinned_memory(
        cpu_padded_slices[:slice_limit], streams
    )

    for i in range(n_images):

        # Synchronise and use the current stream
        streams[i % slice_limit].synchronize()
        streams[i % slice_limit].use()

        # Overwrite the contents of the GPu arrays
        _replace_gpu_array_contents(
            gpu_data_slices[i % slice_limit], data[i], streams[i % slice_limit]
        )
        _replace_gpu_array_contents(
            gpu_padded_data[i % slice_limit],
            cpu_padded_slices[i],
            streams[i % slice_limit],
        )

        # Synchronise the current stream to ensure that the overwriting is complete
        streams[i % slice_limit].synchronize()

        # Perform a median filter on the individual image
        cupy_two_dim_median_filter(
            gpu_data_slices[i % slice_limit], gpu_padded_data[i % slice_limit], size
        )

        # Synchronise to ensure that the GPU median filter has completed
        streams[i % slice_limit].synchronize()

        # Transfer the GPU result to a CPU array
        result[i][:] = gpu_data_slices[i % slice_limit].get(streams[i % slice_limit])

        progress.update()

    progres.mark_complete()

    # Free memory once the operation is complete
    free_memory_pool(gpu_data_slices + gpu_padded_data)

    return result


def _get_padding_value(self, filter_size):
    return filter_size // 2
