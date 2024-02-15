# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock
from typing import TYPE_CHECKING

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.roi_normalisation import RoiNormalisationFilter
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.test_helpers.start_qapplication import start_multiprocessing_pool

if TYPE_CHECKING:
    from mantidimaging.core.data.imagestack import ImageStack


@start_multiprocessing_pool
class ROINormalisationTest(unittest.TestCase):
    """
    Test contrast ROI normalisation filter.

    Tests return value and in-place modified data.
    """

    def test_exception_raised_for_empty_roi_param(self):
        images = th.generate_images()

        air = None

        npt.assert_raises(ValueError, RoiNormalisationFilter.filter_func, images, air)

    def test_not_executed_invalid_shape(self):
        images = np.arange(100).reshape(10, 10)
        air = [3, 3, 4, 4]
        npt.assert_raises(ValueError, RoiNormalisationFilter.filter_func, images, air)

    def test_executed_par(self):
        self.do_execute(th.generate_images_for_parallel(seed=2021))

    def test_executed_seq(self):
        self.do_execute(th.generate_images(seed=2021))

    def do_execute(self, images: ImageStack):
        original = np.copy(images.data[0])

        air = SensibleROI.from_list([3, 3, 4, 4])
        result = RoiNormalisationFilter.filter_func(images, air)

        th.assert_not_equals(result.data[0], original)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        images = th.generate_images()
        roi_mock = mock.Mock()
        roi_mock.text.return_value = "0, 0, 5, 5"
        mode_mock = mock.Mock()
        mode_mock.currentText.return_value = "Stack Average"
        flat_mock = mock.Mock()
        RoiNormalisationFilter.execute_wrapper(roi_mock, mode_mock, flat_mock)(images)
        roi_mock.text.assert_called_once()

    def test_roi_normalisation_stack_average(self):
        air = [3, 3, 6, 8]
        images = th.generate_images([10, 20, 30], seed=2021)
        images.data[2] *= 2
        images.data[3] *= 0.5
        air_data_orig = np.copy(images.data[:, air[1]:air[3], air[0]:air[2]])

        original = np.copy(images.data[0])
        result = RoiNormalisationFilter.filter_func(images, air, "Stack Average")

        air_data_after = np.copy(result.data[:, air[1]:air[3], air[0]:air[2]])

        th.assert_not_equals(result.data[0], original)
        self.assertAlmostEqual(air_data_orig.mean(), air_data_after.mean(), places=6)
        self.assertAlmostEqual(air_data_after[0].mean(), air_data_after[1].mean(), places=6)

    def test_roi_normalisation_to_flat(self):
        air = [3, 3, 6, 8]
        images = th.generate_images([10, 20, 30], seed=2021)
        flat_field = th.generate_images([2, 20, 30], seed=2021)
        images.data[::2] *= 0.5

        air_data_flat = np.copy(flat_field.data[:, air[1]:air[3], air[0]:air[2]])

        original = np.copy(images.data[0])
        result = RoiNormalisationFilter.filter_func(images, air, "Flat Field", flat_field)

        air_data_after = np.copy(result.data[:, air[1]:air[3], air[0]:air[2]])

        th.assert_not_equals(result.data[0], original)
        self.assertAlmostEqual(air_data_flat.mean(), air_data_after.mean(), places=6)
        self.assertAlmostEqual(air_data_after[0].mean(), air_data_after[1].mean(), places=6)

    def test_execute_wrapper_bad_roi_raises_valueerror(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        roi_mock = mock.Mock()
        roi_mock.text.return_value = "apples"
        mode_mock = mock.Mock()
        flat_mock = mock.Mock()
        self.assertRaises(ValueError, RoiNormalisationFilter.execute_wrapper, roi_mock, mode_mock, flat_mock)
        roi_mock.text.assert_called_once()

    def test_filter_func_raises_missing_flat_field(self):
        images_mock = mock.Mock()
        roi_mock = mock.Mock()
        mode_val = "Flat Field"
        flat_val = None
        self.assertRaises(ValueError, RoiNormalisationFilter.filter_func, images_mock, roi_mock, mode_val, flat_val)

    def test_filter_func_raises_bad_mode(self):
        images_mock = mock.Mock()
        roi_mock = mock.Mock()
        mode_val = "Bad mode"
        flat_val = mock.Mock()
        self.assertRaises(ValueError, RoiNormalisationFilter.filter_func, images_mock, roi_mock, mode_val, flat_val)


if __name__ == '__main__':
    unittest.main()
