# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.clip_values import ClipValuesFilter


class ClipValuesFilterTest(unittest.TestCase):
    """
    Test clip values filter.

    Tests return value and in-place modified data.
    """
    def test_exception_raised_for_no_min_or_max(self):
        images = th.generate_images()

        clip_min = None
        clip_max = None

        self.assertRaises(ValueError, ClipValuesFilter.filter_func, images, clip_min, clip_max)

    def test_execute_min_only(self):
        images = th.generate_images()

        result = ClipValuesFilter().filter_func(images,
                                                clip_min=0.2,
                                                clip_max=None,
                                                clip_min_new_value=0.1,
                                                clip_max_new_value=None)

        npt.assert_approx_equal(result.data.min(), 0.1)

    def test_execute_max_only(self):
        images = th.generate_images()

        result = ClipValuesFilter().filter_func(images,
                                                clip_min=None,
                                                clip_max=0.8,
                                                clip_min_new_value=None,
                                                clip_max_new_value=0.9)

        npt.assert_approx_equal(result.data.max(), 0.9)

    def test_execute_min_max(self):
        images = th.generate_images()

        result = ClipValuesFilter().filter_func(images,
                                                clip_min=0.2,
                                                clip_max=0.8,
                                                clip_min_new_value=0.1,
                                                clip_max_new_value=0.9)

        npt.assert_approx_equal(result.data.min(), 0.1)
        npt.assert_approx_equal(result.data.max(), 0.9)

    def test_execute_min_max_no_new_values(self):
        images = th.generate_images()
        result = ClipValuesFilter().filter_func(images,
                                                clip_min=0.2,
                                                clip_max=0.8,
                                                clip_min_new_value=None,
                                                clip_max_new_value=None)

        npt.assert_approx_equal(result.data.min(), 0.2)
        npt.assert_approx_equal(result.data.max(), 0.8)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        # All widget arguments can use identical mocks for this test
        mocks = [mock.Mock() for _ in range(4)]
        for mock_widget in mocks:
            mock_widget.value = mock.Mock(return_value=0)
        execute_func = ClipValuesFilter().execute_wrapper(*mocks)

        images = th.generate_images()
        execute_func(images)

        for mock_widget in mocks:
            self.assertEqual(mock_widget.value.call_count, 1)


if __name__ == '__main__':
    unittest.main()
