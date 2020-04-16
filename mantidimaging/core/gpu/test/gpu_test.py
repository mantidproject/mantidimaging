import unittest
from unittest import mock

import numpy as np
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

    @unittest.skipIf(GPU_NOT_AVAIL, reason=GPU_SKIP_REASON)
    def test_numpy_pad_modes_match_scipy_median_modes(self):

        size = 3
        for mode in modes():
            with self.subTest(mode=mode):

                np.random.seed(10)

                # images = th.gen_img_shared_array_and_copy()[0]
                images = np.random.uniform(low=0.0, high=10.0, size=(2, 3, 3))
                gpu_images = images.copy()
                cpu_images = images.copy()

                gpu_result = MedianFilter.filter_func(gpu_images, size, mode)

                with mock.patch(GPU_UTILITY_LOC, return_value=False):
                    th.switch_mp_off()
                    cpu_result = MedianFilter.filter_func(cpu_images, size, mode)
                    th.switch_mp_on()
                    print(cpu_result == images)
                    print(images)

                npt.assert_almost_equal(gpu_result[0], cpu_result[0])

    @unittest.skipIf(True, reason=GPU_SKIP_REASON)
    def test_gpu_result_matches_cpu_result_for_different_filter_sizes(self):

        mode = "reflect"
        for size in [5, 7, 9]:
            with self.subTest(size=size):

                images = th.gen_img_shared_array_and_copy()[0]

                gpu_result = MedianFilter.filter_func(images.copy(), size, mode)

                with mock.patch(GPU_UTILITY_LOC, return_value=False):
                    cpu_result = MedianFilter.filter_func(images.copy(), size, mode)

                npt.assert_almost_equal(gpu_result, cpu_result)

    @unittest.skipIf(True, reason=GPU_SKIP_REASON)
    def test_gpu_result_matches_cpu_result_for_larger_images(self):

        N = 1000
        size = 3
        mode = "reflect"

        images = np.random.uniform(low=0.0, high=100.0, size=(5, N, N))

        gpu_result = MedianFilter.filter_func(images.copy(), size, mode)

        with mock.patch(GPU_UTILITY_LOC, return_value=False):
            cpu_result = MedianFilter.filter_func(images.copy(), size, mode)

        npt.assert_almost_equal(gpu_result, cpu_result)


if __name__ == "__main__":
    unittest.main()
