# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

import numpy.testing as npt
from parameterized import parameterized

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.rotate_stack import RotateFilter
from mantidimaging.test_helpers.start_qapplication import start_multiprocessing_pool
from mantidimaging.core.operations.rotate_stack.rotate_stack import _get_cardinal_angle, _do_rotation


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

    @parameterized.expand([
        ("0_deg", 0, 0),
        ("44_deg", 44, 0),
        ("45_deg", 45, 0),
        ("46_deg", 46, 90),
        ("134_deg", 134, 90),
        ("135_deg", 135, 180),
        ("136_deg", 136, 180),
        ("224_deg", 224, 180),
        ("225_deg", 225, 180),
        ("226_deg", 226, 270),
        ("314_deg", 314, 270),
        ("316_deg", 316, 0),
        ("360_deg", 360, 0),
    ])
    def test_WHEN_trivial_angle_THEN_closest_cardinal_angle_returned(self, _, general_angle, cardinal_angle):
        self.assertEqual(_get_cardinal_angle(general_angle), cardinal_angle)

    def test_WHEN_compute_rotation_called_WITH_angle_THEN_data_rotated_and_aspect_ratio_changed(self):
        """
        Test that when _compute_rotation is called with an angle then the data is rotated
        """

        images = th.generate_images([5, 6, 7])
        _do_rotation(images, 90, mock.Mock())
        self.assertNotEqual([5, 7, 6], images.data.shape)

    def test_WHEN_compute_rotation_called_WITH_angle_THEN_data_aspect_ratio_remains_the_same(self):
        """
        Test that when _compute_rotation is called with an angle then the data is rotated
        """
        data = th.generate_images()
        shape = data.data.shape
        result = _do_rotation(data, 180, mock.Mock())
        self.assertEqual(result.data.shape, shape)


if __name__ == '__main__':
    unittest.main()
