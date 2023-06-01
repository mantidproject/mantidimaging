# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.rotate_stack import RotateFilter
from mantidimaging.test_helpers.start_qapplication import start_multiprocessing_pool


@start_multiprocessing_pool
class RotateStackTest(unittest.TestCase):
    """
    Test rotate stack filter.

    Tests return value and in-place modified data.
    """

    def test_raise_exception_for_none_angle(self):
        images = th.generate_images()

        rotation = None

        self.assertRaises(ValueError, RotateFilter.filter_func, images, rotation)

    def test_executed_par(self):
        self.do_execute(True)

    def test_executed_seq(self):
        self.do_execute(False)

    def do_execute(self, in_parallel):
        # only works on square images
        if in_parallel:
            images = th.generate_images_for_parallel((15, 15, 15))
        else:
            images = th.generate_images((10, 10, 10))

        rotation = -90
        images.data[:, 0, :] = 42

        result = RotateFilter.filter_func(images, rotation)

        npt.assert_equal(result.data[:, :, -1], 42)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        rotation_count = mock.Mock()
        rotation_count.value = mock.Mock(return_value=0)
        execute_func = RotateFilter.execute_wrapper(rotation_count)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(rotation_count.value.call_count, 1)


if __name__ == '__main__':
    unittest.main()
