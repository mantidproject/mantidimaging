# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from parameterized import parameterized
import unittest
from unittest import mock

import numpy as np

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.gaussian import GaussianFilter


class GaussianTest(unittest.TestCase):
    """
    Test gaussian filter.

    Tests return value and in-place modified data.

    Surprisingly sequential Gaussian seems to outperform parallel Gaussian on
    very small data.

    This does not scale and parallel execution is always faster on any
    reasonably sized data (e.g. 143,512,512)
    """
    @parameterized.expand([("None", None), ("1", 1)])
    def test_exception_raised_for_invalid_size(self, _, size):
        images = th.generate_images()

        mode = None
        order = None

        self.assertRaises(ValueError, GaussianFilter.filter_func, images, size, mode, order)

    def test_executed_parallel(self):
        images = th.generate_images()

        size = 3
        mode = 'reflect'
        order = 1

        original = np.copy(images.data[0])
        result = GaussianFilter.filter_func(images, size, mode, order)

        th.assert_not_equals(result.data, original)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        size_field = mock.Mock()
        size_field.value = mock.Mock(return_value=2)
        mode_field = mock.Mock()
        mode_field.currentText = mock.Mock(return_value='reflect')
        order_field = mock.Mock()
        order_field.value = mock.Mock(return_value=0)
        execute_func = GaussianFilter.execute_wrapper(size_field, order_field, mode_field)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(size_field.value.call_count, 1)
        self.assertEqual(mode_field.currentText.call_count, 1)
        self.assertEqual(order_field.value.call_count, 1)


if __name__ == '__main__':
    unittest.main()
