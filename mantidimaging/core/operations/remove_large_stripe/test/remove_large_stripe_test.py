# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.test_helpers.start_qapplication import setup_shared_memory_manager
from mantidimaging.core.operations.remove_large_stripe import RemoveLargeStripesFilter


@setup_shared_memory_manager
class RemoveLargeStripesTest(unittest.TestCase):
    """
    Test stripe removal filter.

    Tests that it executes and returns a valid object, but does not verify the numerical results.
    """
    def test_executed(self):
        images = th.generate_images()
        control = images.copy()

        result = RemoveLargeStripesFilter.filter_func(images)

        th.assert_not_equals(result.data, control.data)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        snr = mock.Mock()
        snr.value = mock.Mock(return_value=3)
        la_size = mock.Mock()
        la_size.value = mock.Mock(return_value=61)
        execute_func = RemoveLargeStripesFilter.execute_wrapper(snr, la_size)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(snr.value.call_count, 1)
        self.assertEqual(la_size.value.call_count, 1)


if __name__ == '__main__':
    unittest.main()
