# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest

from unittest import mock
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.crop_coords import CropCoordinatesFilter
from mantidimaging.core.utility.sensible_roi import SensibleROI


class CropCoordsTest(unittest.TestCase):
    """
    Test crop by coordinates filter.

    Tests return value only.
    """
    def test_executed_only_volume(self):
        # Check that the filter is  executed when:
        #   - valid Region of Interest is provided
        #   - no flat or dark images are provided
        roi = SensibleROI.from_list([1, 1, 5, 5])
        images = th.generate_images()
        # store references here so that they don't get freed inside the filter execute
        sample = images.shared_array
        result = CropCoordinatesFilter.filter_func(images, roi)
        expected_shape = (10, 4, 4)

        npt.assert_equal(result.data.shape, expected_shape)
        # check that the data has been modified
        th.assert_not_equals(result.data, sample.array)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        images = th.generate_images()
        roi_mock = mock.Mock()
        roi_mock.text.return_value = "0, 0, 5, 5"
        CropCoordinatesFilter.execute_wrapper(roi_mock)(images)
        roi_mock.text.assert_called_once()

    def test_execute_wrapper_bad_roi_raises_valueerror(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        roi_mock = mock.Mock()
        roi_mock.text.return_value = "apples"
        self.assertRaises(ValueError, CropCoordinatesFilter.execute_wrapper, roi_mock)
        roi_mock.text.assert_called_once()


if __name__ == '__main__':
    unittest.main()
