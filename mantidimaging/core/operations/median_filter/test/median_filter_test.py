# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from parameterized import parameterized
import unittest
from unittest import mock
from typing import TYPE_CHECKING

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.gpu import utility as gpu
from mantidimaging.core.operations.median_filter import MedianFilter
from mantidimaging.test_helpers.start_qapplication import start_multiprocessing_pool

if TYPE_CHECKING:
    from mantidimaging.core.data.imagestack import ImageStack

GPU_UTIL_LOC = "mantidimaging.core.gpu.utility.gpu_available"


@start_multiprocessing_pool
class MedianTest(unittest.TestCase):
    """
    Test median filter.

    Tests return value and in-place modified data.
    """
    @parameterized.expand([("None", None), ("1", 1)])
    def test_exception_raised_for_invalid_size(self, _, size):
        images = th.generate_images()

        mode = None

        npt.assert_raises(ValueError, MedianFilter.filter_func, images, size, mode)

    def test_executed_no_helper_parallel(self):
        images = th.generate_images()

        size = 3
        mode = 'reflect'

        original = np.copy(images.data[0])
        result = MedianFilter.filter_func(images, size, mode)

        th.assert_not_equals(result.data, original)

    @unittest.skipIf(not gpu.gpu_available(), reason="Skip GPU tests if cupy isn't installed")
    def test_executed_no_helper_gpu(self):
        images = th.generate_images()

        size = 3
        mode = 'reflect'

        original = np.copy(images.data[0])
        result = MedianFilter.filter_func(images, size, mode, force_cpu=False)

        th.assert_not_equals(result.data, original)

    def test_executed_seq(self):
        self.do_execute(th.generate_images())

    def test_executed_par(self):
        self.do_execute(th.generate_images_for_parallel())

    def do_execute(self, images: ImageStack):
        size = 3
        mode = 'reflect'

        original = np.copy(images.data[0])
        result = MedianFilter.filter_func(images, size, mode)
        th.assert_not_equals(result.data, original)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        size_field = mock.Mock()
        size_field.value = mock.Mock(return_value=3)
        mode_field = mock.Mock()
        mode_field.currentText = mock.Mock(return_value='reflect')
        use_gpu_field = mock.Mock()
        use_gpu_field.isChecked = mock.Mock(return_value=False)
        execute_func = MedianFilter.execute_wrapper(size_field, mode_field, use_gpu_field)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(size_field.value.call_count, 1)
        self.assertEqual(mode_field.currentText.call_count, 1)
        self.assertEqual(use_gpu_field.isChecked.call_count, 1)

    @parameterized.expand([("CPU", True), ("GPU", False)])
    def test_executed_with_nan(self, _, use_cpu):
        if not use_cpu and not gpu.gpu_available():
            self.skipTest(reason="Skip GPU tests if cupy isn't installed")
        shape = (1, 20, 20)
        images = th.generate_images(shape=shape, seed=2021)

        images.data[0, 0, 1] = np.nan  # single edge
        images.data[0, 4, 4] = np.nan  # single
        images.data[0, 4, 7] = np.nan  # diagonal neighbours
        images.data[0, 5, 8] = np.nan
        images.data[0, 7:9, 2:4] = np.nan  # 2x2 block
        images.data[0, 7:9, 6:9] = np.nan  # 2x3
        images.data[0, 12:15, 2:5] = np.nan  # 3x3
        self.assertTrue(np.any(np.isnan(images.data)))

        images_copy = images.copy()
        result = MedianFilter.filter_func(images_copy, 3, 'reflect', force_cpu=use_cpu)

        npt.assert_equal(np.isnan(result.data), np.isnan(images.data))


if __name__ == '__main__':
    unittest.main()
