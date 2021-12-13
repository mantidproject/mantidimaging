# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.rotate_stack import RotateFilter


class RotateStackTest(unittest.TestCase):
    """
    Test rotate stack filter.

    Tests return value and in-place modified data.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_executed_par(self):
        self.do_execute()

    def test_executed_seq(self):
        self.do_execute(cores=1)

    def do_execute(self, cores=None):
        # only works on square images
        images = th.generate_images((10, 10, 10))

        rotation = -90
        images.data[:, 0, :] = 42

        result = RotateFilter.filter_func(images, rotation, cores=cores)

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
