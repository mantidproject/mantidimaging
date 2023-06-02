# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from parameterized import parameterized
import unittest
from unittest import mock

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.circular_mask import CircularMaskFilter


class CircularMaskTest(unittest.TestCase):
    """
    Test circular mask filter.

    Tests return value and in-place modified data.
    """

    @parameterized.expand([("None", None), ("0", 0), ("1", 1)])
    def test_exception_raised_for_invalid_ratio(self, _, ratio):
        images = th.generate_images()

        self.assertRaises(ValueError, CircularMaskFilter.filter_func, images, ratio)

    def test_executed(self):
        images = th.generate_images()

        ratio = 0.9

        self.assertNotEqual(images.data[0, 0, 0], 0)
        self.assertNotEqual(images.data[0, 0, -1], 0)

        result = CircularMaskFilter.filter_func(images, ratio)
        self.assertEqual(result.data[0, 0, 0], 0)
        self.assertEqual(result.data[0, 0, -1], 0)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        radius_field = mock.Mock()
        radius_field.value = mock.Mock(return_value=0.95)
        value_field = mock.Mock()
        value_field.value = mock.Mock(return_value=0)
        execute_func = CircularMaskFilter.execute_wrapper(radius_field, value_field)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(radius_field.value.call_count, 1)
        self.assertEqual(value_field.value.call_count, 1)


if __name__ == '__main__':
    unittest.main()
