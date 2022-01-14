# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest

from unittest import mock
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.median_filter import MedianFilter, modes
from mantidimaging.core.gpu import utility as gpu

GPU_NOT_AVAIL = not gpu.gpu_available()
GPU_SKIP_REASON = "Skip GPU tests if cupy isn't installed."
GPU_UTILITY_LOC = "mantidimaging.core.gpu.utility.gpu_available"


class GPUTest(unittest.TestCase):
    """
    Test median filter.

    Tests return value and in-place modified data.
    """
    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_numpy_pad_modes_match_scipy_median_modes(self):
        """
        Run the median filter on the GPU and CPU with the different scipy modes. Check that the results match.
        Should demonstrate that the arguments passed to numpy pad are the correct equivalents to the scipy modes.
        """
        size = 3
        for mode in modes():
            with self.subTest(mode=mode):

                images = th.generate_images()

                gpu_result = MedianFilter.filter_func(images.copy(), size, mode, force_cpu=False)
                cpu_result = MedianFilter.filter_func(images.copy(), size, mode, force_cpu=True)

                npt.assert_almost_equal(gpu_result.data[0], cpu_result.data[0])

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_gpu_result_matches_cpu_result_for_different_filter_sizes(self):
        """
        Run the median filter on the CPU and GPU with different filter sizes. Check that the results match.
        """
        mode = "reflect"
        for size in [5, 7, 9]:
            with self.subTest(size=size):

                images = th.generate_images()

                gpu_result = MedianFilter.filter_func(images.copy(), size, mode, force_cpu=False)
                cpu_result = MedianFilter.filter_func(images.copy(), size, mode, force_cpu=True)

                npt.assert_almost_equal(gpu_result.data, cpu_result.data)

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_gpu_result_matches_cpu_result_for_larger_images(self):
        """
        Run the median filter on the CPU and GPU with a larger image size. Check that the results match. This test may
        reveal issues such as the grid and dimension size arguments going wrong.
        """
        N = 1200
        size = 3
        mode = "reflect"

        images = th.generate_images(shape=(20, N, N))

        gpu_result = MedianFilter.filter_func(images.copy(), size, mode, force_cpu=False)
        cpu_result = MedianFilter.filter_func(images.copy(), size, mode, force_cpu=True)

        npt.assert_almost_equal(gpu_result.data, cpu_result.data)

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_double_is_used_in_cuda_for_float_64_arrays(self):
        """
        Run the median filter on the CPU and GPU with a float64 array. This demonstrates that replacing instances of
        'float' with 'double' in the CUDA file is doing the right thing.
        """
        size = 3
        mode = "reflect"
        images = th.generate_images(dtype="float64")

        gpu_result = MedianFilter.filter_func(images.copy(), size, mode, force_cpu=False)
        cpu_result = MedianFilter.filter_func(images.copy(), size, mode, force_cpu=True)

        npt.assert_almost_equal(gpu_result.data, cpu_result.data)

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_image_slicing_works(self):
        """
        Run the median filter on the CPU and GPU with an image stack that is larger than the limit permitted on the GPU.
        This demonstrates that the algorithm for slicing the stack and overwriting GPU arrays is working correctly.
        """
        N = 30
        size = 3
        mode = "reflect"

        # Make the number of images in the stack exceed the maximum number of GPU-stored images
        n_images = gpu.MAX_GPU_SLICES * 3

        images = th.generate_images(shape=(n_images, N, N))

        gpu_result = MedianFilter.filter_func(images.copy(), size, mode, force_cpu=False)
        cpu_result = MedianFilter.filter_func(images.copy(), size, mode, force_cpu=True)

        npt.assert_almost_equal(gpu_result.data, cpu_result.data)

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_array_input_unchanged_when_gpu_runs_out_of_memory(self):
        """
        Mock the GPU running out of memory. Check that this leaves the input array to be unchanged.
        """
        import cupy as cp

        N = 200
        n_images = 2000
        size = 3
        mode = "reflect"

        images = th.generate_images(shape=(n_images, N, N))

        with mock.patch("mantidimaging.core.gpu.utility._send_single_array_to_gpu",
                        side_effect=cp.cuda.memory.OutOfMemoryError(0, 0)):
            gpu_result = MedianFilter.filter_func(images, size, mode, force_cpu=False)

        assert gpu_result == images

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_gpu_running_out_of_memory_causes_free_memory_to_be_called(self):
        """
        Mock the GPU running out of memory. Check that this causes the free memory block function to be called.
        """
        import cupy as cp

        N = 20
        n_images = 2

        images = th.generate_images(shape=(n_images, N, N))

        with mock.patch("mantidimaging.core.gpu.utility._send_single_array_to_gpu",
                        side_effect=cp.cuda.memory.OutOfMemoryError(0, 0)):
            with mock.patch("mantidimaging.core.gpu.utility._free_memory_pool") as mock_free_gpu:
                gpu._send_arrays_to_gpu_with_pinned_memory(images.data, [cp.cuda.Stream() for _ in range(n_images)])

        mock_free_gpu.assert_called()


if __name__ == "__main__":
    unittest.main()
