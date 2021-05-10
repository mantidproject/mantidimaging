# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

import numpy as np

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.data.images import Images
from mantidimaging.core.gpu import utility as gpu
from mantidimaging.core.operations.median_filter import MedianFilter

GPU_UTIL_LOC = "mantidimaging.core.gpu.utility.gpu_available"


class MedianTest(unittest.TestCase):
    """
    Test median filter.

    Tests return value and in-place modified data.
    """
    def __init__(self, *args, **kwargs):
        super(MedianTest, self).__init__(*args, **kwargs)

    def test_not_executed(self):
        images = th.generate_images()

        size = None
        mode = None

        original = np.copy(images.data[0])
        result = MedianFilter.filter_func(images, size, mode)

        th.assert_not_equals(result.data, original)

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

    def do_execute(self, images: Images):
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
        size_field.value = mock.Mock(return_value=0)
        mode_field = mock.Mock()
        mode_field.currentText = mock.Mock(return_value=0)
        use_gpu_field = mock.Mock()
        use_gpu_field.isChecked = mock.Mock(return_value=False)
        execute_func = MedianFilter.execute_wrapper(size_field, mode_field, use_gpu_field)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(size_field.value.call_count, 1)
        self.assertEqual(mode_field.currentText.call_count, 1)
        self.assertEqual(use_gpu_field.isChecked.call_count, 1)


if __name__ == '__main__':
    unittest.main()
