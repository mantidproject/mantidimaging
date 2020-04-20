import unittest

from unittest import mock
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.median_filter import MedianFilter, modes
from mantidimaging.core.gpu import utility as gpu

GPU_NOT_AVAIL = not gpu.gpu_available()
GPU_SKIP_REASON = "Skip GPU tests if cupy isn't installed."
GPU_UTILITY_LOC = "mantidimaging.core.gpu.utility.gpu_available"


class GPUTest(unittest.TestCase):
    """
    Test median filter.

    Tests return value and in-place modified data.
    """
    def __init__(self, *args, **kwargs):
        super(GPUTest, self).__init__(*args, **kwargs)
        if not GPU_NOT_AVAIL:
            self.cuda = gpu.CudaExecuter("float32")

    @staticmethod
    def run_serial(data, size, mode):
        th.switch_mp_off()
        cpu_result = MedianFilter.filter_func(data, size, mode)
        th.switch_mp_on()
        return cpu_result

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_numpy_pad_modes_match_scipy_median_modes(self):

        size = 3
        for mode in modes():
            with self.subTest(mode=mode):

                images = th.gen_img_shared_array()

                gpu_result = MedianFilter.filter_func(images.copy(), size, mode, self.cuda)
                cpu_result = self.run_serial(images.copy(), size, mode)

                npt.assert_almost_equal(gpu_result[0], cpu_result[0])

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_gpu_result_matches_cpu_result_for_different_filter_sizes(self):

        mode = "reflect"
        for size in [5, 7, 9]:
            with self.subTest(size=size):

                images = th.gen_img_shared_array()

                gpu_result = MedianFilter.filter_func(images.copy(), size, mode, self.cuda)
                cpu_result = self.run_serial(images.copy(), size, mode)

                npt.assert_almost_equal(gpu_result, cpu_result)

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_gpu_result_matches_cpu_result_for_larger_images(self):

        N = 1200
        size = 3
        mode = "reflect"

        images = th.gen_img_shared_array(shape=(20, N, N))

        gpu_result = MedianFilter.filter_func(images.copy(), size, mode, self.cuda)
        cpu_result = self.run_serial(images.copy(), size, mode)

        npt.assert_almost_equal(gpu_result, cpu_result)

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_double_is_used_in_cuda_for_float_64_arrays(self):

        size = 3
        mode = "reflect"
        images = th.gen_img_shared_array(dtype="float64")
        cuda = gpu.CudaExecuter("float64")

        gpu_result = MedianFilter.filter_func(images.copy(), size, mode, cuda)
        cpu_result = self.run_serial(images.copy(), size, mode)

        npt.assert_almost_equal(gpu_result, cpu_result)

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_image_slicing_works(self):

        N = 30
        n_images = gpu.MAX_GPU_SLICES * 3
        size = 3
        mode = "reflect"

        images = th.gen_img_shared_array(shape=(n_images, N, N))

        gpu_result = MedianFilter.filter_func(images.copy(), size, mode, self.cuda)
        cpu_result = self.run_serial(images.copy(), size, mode)

        npt.assert_almost_equal(gpu_result, cpu_result)

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_array_input_unchanged_when_gpu_runs_out_of_memory(self):

        import cupy as cp

        N = 200
        n_images = 2000
        size = 3
        mode = "reflect"

        images = th.gen_img_shared_array(shape=(n_images, N, N))

        with mock.patch("mantidimaging.core.gpu.utility._send_single_array_to_gpu",
                        side_effect=cp.cuda.memory.OutOfMemoryError(0, 0)):
            gpu_result = MedianFilter.filter_func(images.copy(), size, mode, self.cuda)

        npt.assert_equal(gpu_result, images)

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_gpu_running_out_of_memory_causes_free_memory_to_be_called(self):

        import cupy as cp

        N = 200
        n_images = 2000
        size = 3
        mode = "reflect"

        images = th.gen_img_shared_array(shape=(n_images, N, N))

        with mock.patch("mantidimaging.core.gpu.utility._send_single_array_to_gpu",
                        side_effect=cp.cuda.memory.OutOfMemoryError(0, 0)):
            with mock.patch("mantidimaging.core.gpu.utility._free_memory_pool") as mock_free_gpu:
                MedianFilter.filter_func(images.copy(), size, mode, self.cuda)

        mock_free_gpu.assert_called()


if __name__ == "__main__":
    unittest.main()
