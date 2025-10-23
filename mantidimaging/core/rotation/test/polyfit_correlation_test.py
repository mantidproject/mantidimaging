# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from unittest import mock
import numpy as np
import numpy.testing as npt

from mantidimaging.core.utility.data_containers import ProjectionAngles
from mantidimaging.test_helpers.start_qapplication import start_multiprocessing_pool
from mantidimaging.test_helpers.unit_test_helper import generate_images
from ..polyfit_correlation import do_calculate_correlation_err, get_search_range, find_center, _find_shift
from ...utility.progress_reporting import Progress


@start_multiprocessing_pool
class PolyfitCorrelationTest(unittest.TestCase):

    def test_do_search(self):
        test_p0 = np.identity(10)
        test_p180 = np.fliplr(test_p0)

        search_range = get_search_range(test_p0.shape[1])
        result = []
        do_calculate_correlation_err(result, search_range[0], (test_p0, test_p180), test_p0.shape[1])
        expected = [0.2, 0.2, 0.0, 0.2, 0.2, 0.2, 0.2, 0.0, 0.2, 0.2]
        assert result == expected, f"Found {result}"

        do_calculate_correlation_err(result, search_range[1], (test_p0, test_p180), test_p0.shape[1])
        expected = [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]
        assert result == expected, f"Found {result}"

        do_calculate_correlation_err(result, search_range[8], (test_p0, test_p180), test_p0.shape[1])
        expected = [0.2, 0.2, 0.2, 0.0, 0.2, 0.2, 0.2, 0.2, 0.0, 0.2]
        assert result == expected, f"Found {result}"

    def test_find_center(self):
        images = generate_images((10, 10, 10))
        images.data[0] = np.identity(10)
        images.data[1] = np.fliplr(images.data[0])
        images.set_projection_angles(ProjectionAngles(np.array([0, 180] + [0] * 8)))
        mock_progress = mock.create_autospec(Progress, instance=True)
        res_cor, res_tilt = find_center(images, 0, 1, mock_progress)
        assert mock_progress.update.call_count == images.height + 1
        assert res_cor.value == 5.0, f"Found {res_cor.value}"
        assert abs(res_tilt.value) < 1e-6, f"Found {res_tilt.value}"

    def test_find_center_offset(self):
        images = generate_images((10, 10, 10))
        images.data[0] = np.identity(10)
        images.data[1] = np.fliplr(images.data[0])
        self.crop_images(images, (2, 10, 0, 10))  # Crops to 8 rows
        images.set_projection_angles(ProjectionAngles(np.array([0, 180] + [0] * 8)))
        mock_progress = mock.create_autospec(Progress, instance=True)
        find_center(images, 0, 1, mock_progress)
        assert mock_progress.update.call_count > 0

    def test_find_shift(self):
        images = mock.Mock(height=3)
        min_correlation_error = np.array([[1, 2, 2, 2, 2, 2, 2, 2, 2, 2], [3, 3, 3, 3, 3, 3, 3, 3, 2, 3],
                                          [4, 4, 4, 4, 3, 4, 4, 4, 4, 4]]).T
        search_range = get_search_range(10)
        shift = np.zeros(3)
        _find_shift(images, search_range, min_correlation_error, shift)
        npt.assert_array_equal(np.array([-5, 3, -1]), shift)

    def test_find_shift_multiple_argmin(self):
        images = mock.Mock(height=3)
        min_correlation_error = np.array([[1, 2, 2, 2, 2, 2, 2, 2, 2, 1], [3, 3, 3, 3, 3, 3, 3, 3, 2, 2],
                                          [4, 4, 4, 4, 3, 3, 4, 4, 4, 4]]).T
        search_range = get_search_range(10)
        shift = np.zeros(3)
        _find_shift(images, search_range, min_correlation_error, shift)
        npt.assert_array_equal(np.array([-5, 3, -1]), shift)

    @staticmethod
    def crop_images(images, crop_coords):
        x_start, x_end, y_start, y_end = crop_coords
        images.data = images.data[:, y_start:y_end, x_start:x_end]


if __name__ == '__main__':
    unittest.main()
