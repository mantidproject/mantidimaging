import unittest
from unittest import mock

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.median_filter import MedianFilter, modes
from mantidimaging.core.gpu import utility as gpu


class GPUTest(unittest.TestCase):
    """
    Test median filter.

    Tests return value and in-place modified data.
    """

    def __init__(self, *args, **kwargs):
        super(GPUTest, self).__init__(*args, **kwargs)

    @unittest.skipIf(
        not gpu.gpu_available(), reason="Skip GPU tests if cupy isn't installed"
    )
    def test_numpy_pad_modes_match_scipy_median_modes(self):

        for mode in modes():
            with self.subTest(mode=mode):

                images = th.gen_img_shared_array_and_copy()[0]

                size = 3
                th.switch_gpu_off()
                cpu_result = MedianFilter.filter_func(images.copy(), size, mode)
                th.switch_gpu_on()
                gpu_result = MedianFilter.filter_func(images.copy(), size, mode)

                npt.assert_equal(gpu_result, cpu_result)

    def test_gpu_result_matches_cpu_result_for_different_filter_sizes(self):

        for size in [5, 7, 9]:
            with self.subTest(size=size):
                images = th.gen_img_shared_array_and_copy()[0]

                mode = "reflect"
                th.switch_gpu_off()
                cpu_result = MedianFilter.filter_func(images.copy(), size, mode)
                th.switch_gpu_on()
                gpu_result = MedianFilter.filter_func(images.copy(), size, mode)

                npt.assert_equal(gpu_result, cpu_result)


if __name__ == "__main__":
    unittest.main()
