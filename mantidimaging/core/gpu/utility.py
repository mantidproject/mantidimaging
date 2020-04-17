import os
import numpy as np

MAX_CUPY_MEMORY_FRACTION = 0.8
FREE_MEMORY_FACTOR = 0.8
MAX_GPU_SLICES = 100
KERNEL_FILENAME = "cuda_image_filters.cu"

try:
    import cupy as cp

    CUPY_INSTALLED = True

    # Initialise the memory pool
    mempool = cp.get_default_memory_pool()
    with cp.cuda.Device(0):
        mempool.set_limit(fraction=MAX_CUPY_MEMORY_FRACTION)

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
    """
    Returns True if cupy is installed, False otherwise.
    """
    return CUPY_INSTALLED


def _load_cuda_kernel(dtype):
    """
    Loads the CUDA kernel so that cupy can act as a mediator. Replaces instances of 'float' with 'double' if the dtype
    is float64.
    :param dtype: The data type of the array that is going to be processed.
    :return: The CUDA kernel in string format.
    """
    cuda_kernel = ""
    with open(os.path.join(os.path.dirname(__file__), KERNEL_FILENAME), "r") as f:
        cuda_kernel += f.read()
    if "float64" in str(dtype):
        return cuda_kernel.replace("float", "double")
    return cuda_kernel


def _free_memory_pool(arrays=[]):
    """
    Delete the existing GPU arrays and frees blocks.
    """
    if arrays:
        arrays.clear()
    mempool.free_all_blocks()


def _create_pinned_memory(cpu_array):
    """
    Use pinned memory in order to store a numpy array on the GPU.
    :param cpu_array: The numpy array to be transferred to the GPU.
    :return: src
    """
    mem = cp.cuda.alloc_pinned_memory(cpu_array.nbytes)
    src = np.frombuffer(mem, cpu_array.dtype, cpu_array.size).reshape(cpu_array.shape)
    src[...] = cpu_array
    return src


def _send_single_array_to_gpu(cpu_array, stream):
    """
    Sends a single array to the GPU using pinned memory and a stream.
    :param cpu_array: The numpy array to be transferred to the GPU.
    :param stream: The stream used to mediate the transfer.
    :return: A GPU array.
    """
    pinned_memory = _create_pinned_memory(cpu_array.copy())
    gpu_array = cp.empty(pinned_memory.shape, dtype=cpu_array.dtype)
    gpu_array.set(pinned_memory, stream=stream)
    return gpu_array


def _send_arrays_to_gpu_with_pinned_memory(cpu_arrays, streams):
    """
    Transfer the arrays to the GPU using pinned memory. Raises an error if the GPU runs out of memory.
    :param cpu_arrays: A list of numpy arrays to be transferred to the GPU.
    :param streams: A list of streams used to mediate the transfers. Needs to have the same length as the cpu_arrays
    list.
    :return: A list of GPU arrays.
    """
    gpu_arrays = []

    try:

        for i in range(len(cpu_arrays)):
            gpu_arrays.append(_send_single_array_to_gpu(cpu_arrays[i], streams[i]))

        return gpu_arrays

    except cp.cuda.memory.OutOfMemoryError:
        print("GPU is out of memory...")
        _free_memory_pool(gpu_arrays)
        return []


def _create_block_and_grid_args(data):
    """
    Create the block and grid arguments that are passed to the cupy. These determine how the array
    is broken up.
    :param data: The array that will be processed using the GPU.
    :return: block_size and grid_size that are passed to the CUDA kernel.
    """
    N = 10
    block_size = tuple(N for _ in range(data.ndim))
    grid_size = tuple((shape // N) + 1 for shape in data.shape)
    return block_size, grid_size


def _create_padded_array(data, filter_size, scipy_mode):
    """
    Creates the padded array on the CPU for the median filter.
    :param data: The data array to be padded.
    :param filter_size: The size of the filter that will be applied to the data array.
    :param scipy_mode: The desired mode for the scipy median filter.
    :return: An padded version of the data array.
    """
    # Use the 'mode' argument that is ordinarily given to 'scipy' and determine its numpy.pad equivalent.
    pad_size = _get_padding_value(filter_size)
    return np.pad(data, pad_width=((pad_size, pad_size), (pad_size, pad_size)), mode=EQUIVALENT_PAD_MODE[scipy_mode])


def _replace_gpu_array_contents(gpu_array, cpu_array, stream):
    """
    Overwrites the contents of an existing GPU array with a given CPU array.
    :param gpu_array: The GPU array to be overwritten.
    :param cpu_array: The CPU array that should be used to overwrite the GPU array.
    :param stream: The stream to mediate the transfer.
    """
    gpu_array.set(cpu_array, stream)


def _get_padding_value(filter_size):
    """
    Determine the padding value by using the filter size.
    :param filter_size: The filter size.
    :return: The size of padding needed for the padded array.
    """
    return filter_size // 2


class CudaExecuter:
    def __init__(self, dtype):

        # Load the CUDA kernel through cupy
        loaded_from_source = _load_cuda_kernel(dtype)
        median_filter_module = cp.RawModule(code=loaded_from_source)
        self.single_image_median_filter = median_filter_module.get_function("two_dimensional_median_filter")

        # Warm up the CUDA functions
        self._warm_up(dtype)

    def _warm_up(self, dtype):
        """
        Runs the median filter on a small test array in order to allow it to compile then deleted the GPU arrays.
        :param dtype: The data type of the input array.
        """
        filter_size = 3
        test_array_size = 10
        padded_array_size = test_array_size + _get_padding_value(filter_size)

        test_data = cp.random.uniform(low=0, high=5, size=(test_array_size, test_array_size)).astype(dtype)
        test_padding = cp.random.uniform(low=0, high=5, size=(padded_array_size, padded_array_size)).astype(dtype)
        self._cuda_single_image_median_filter(test_data, test_padding, filter_size)

        # Clear the test arrays
        _free_memory_pool([test_data, test_padding])

    def _cuda_single_image_median_filter(self, input_data, padded_data, filter_size):
        """
        Run the median filter on a single 2D image using CUDA.
        :param input_data: A 2D GPU data array.
        :param padded_data: The corresponding padded GPU array.
        :param filter_size: The size of the filter.
        """
        block_size, grid_size = _create_block_and_grid_args(input_data)
        self.single_image_median_filter(
            grid_size,
            block_size,
            (
                input_data,
                padded_data,
                input_data.shape[0],
                input_data.shape[1],
                filter_size,
            ),
        )

    def median_filter(self, data, filter_size, mode, progress):
        """
        Runs the median filter on a stack of 2D images asynchronously.
        :param data: The CPU data array containing a stack of 2D images.
        :param filter_size: The filter size.
        :param mode: The mode for the filter. Determines how the edge value are managed.
        :param progress: An object for displaying the filter progress.
        """

        # Try to free memory
        _free_memory_pool()

        n_images = data.shape[0]

        # Set the maximum number of images that will be on the GPU at a time
        if n_images > MAX_GPU_SLICES:
            slice_limit = MAX_GPU_SLICES
        else:
            # If the number of images is smaller than the slice limit, use that instead
            slice_limit = n_images

        cpu_padded_images = [_create_padded_array(data_slice, filter_size, mode) for data_slice in data]
        streams = [cp.cuda.Stream(non_blocking=True) for _ in range(slice_limit)]

        # Send the data arrays and padded arrays to the GPU in slices
        gpu_data_slices = _send_arrays_to_gpu_with_pinned_memory(data[:slice_limit], streams)
        gpu_padded_data = _send_arrays_to_gpu_with_pinned_memory(cpu_padded_images[:slice_limit], streams)

        for i in range(n_images):

            # Synchronise and use the current stream
            streams[i % slice_limit].synchronize()
            streams[i % slice_limit].use()

            # Overwrite the contents of the GPU arrays
            _replace_gpu_array_contents(gpu_data_slices[i % slice_limit], data[i], streams[i % slice_limit])
            _replace_gpu_array_contents(
                gpu_padded_data[i % slice_limit],
                cpu_padded_images[i],
                streams[i % slice_limit],
            )

            # Synchronise the current stream to ensure that the overwriting is complete
            streams[i % slice_limit].synchronize()

            # Apply the median filter on the individual image
            self._cuda_single_image_median_filter(gpu_data_slices[i % slice_limit], gpu_padded_data[i % slice_limit],
                                                  filter_size)

            # Synchronise to ensure that the GPU median filter has completed
            streams[i % slice_limit].synchronize()

            # Transfer the GPU result to a CPU array
            data[i][:] = gpu_data_slices[i % slice_limit].get(streams[i % slice_limit])

            progress.update()

        progress.mark_complete()

        # Free memory once the operation is complete
        _free_memory_pool(gpu_data_slices + gpu_padded_data)

        return data
