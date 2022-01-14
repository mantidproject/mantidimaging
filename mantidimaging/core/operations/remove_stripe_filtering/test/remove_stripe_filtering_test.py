# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.remove_stripe_filtering import RemoveStripeFilteringFilter


class RemoveStripeFilteringTest(unittest.TestCase):
    """
    Test stripe removal filter.

    Tests that it executes and returns a valid object, but does not verify the numerical results.
    """
    def test_executed_1d(self):
        images = th.generate_images()
        control = images.copy()

        result = RemoveStripeFilteringFilter.filter_func(images)

        th.assert_not_equals(result.data, control.data)

    def test_executed_2d(self):
        images = th.generate_images()
        control = images.copy()

        result = RemoveStripeFilteringFilter.filter_func(images, filtering_dim=2)

        th.assert_not_equals(result.data, control.data)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        sigma = mock.Mock()
        sigma.value = mock.Mock(return_value=3)
        size = mock.Mock()
        size.value = mock.Mock(return_value=61)
        window_dim = mock.Mock()
        window_dim.value = mock.Mock(return_value=61)
        filtering_dim = mock.Mock()
        filtering_dim.value = mock.Mock(return_value=61)
        execute_func = RemoveStripeFilteringFilter.execute_wrapper(sigma, size, window_dim, filtering_dim)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(sigma.value.call_count, 1)
        self.assertEqual(size.value.call_count, 1)


if __name__ == '__main__':
    unittest.main()
