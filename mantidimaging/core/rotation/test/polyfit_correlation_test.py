# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock
import numpy as np

# from mantidimaging.test_helpers.start_qapplication import start_multiprocessing_pool
from mantidimaging.test_helpers.unit_test_helper import generate_images, assert_not_equals
from ..polyfit_correlation import do_calculate_correlation_err, get_search_range, find_center, _find_shift
from ...data import ImageStack
from ...utility.progress_reporting import Progress


# @start_multiprocessing_pool
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
        images.proj180deg = ImageStack(np.fliplr(images.data))
        mock_progress = mock.create_autospec(Progress)
        res_cor, res_tilt = find_center(images, mock_progress)
        assert mock_progress.update.call_count == 11
        assert res_cor.value == 5.0, f"Found {res_cor.value}"
        assert res_tilt.value == 0.0, f"Found {res_tilt.value}"

    def test_find_shift(self):
        images = generate_images((10, 10, 10))
        search_range = get_search_range(images.width)
        min_correlation_error = np.random.rand(len(search_range), images.height)
        shift = np.zeros((images.height, ))
        _find_shift(images, search_range, min_correlation_error, shift)
        # check that the shift has been changed
        assert_not_equals(shift, np.zeros((images.height, )))

    def test_find_shift_multiple_argmin(self):
        images = generate_images((10, 10, 10))
        search_range = get_search_range(images.width)
        min_correlation_error = np.random.rand(len(search_range), images.height)
        min_correlation_error.T[0][3] = min_correlation_error.T[0][4] = 0
        shift = np.zeros((images.height, ))
        _find_shift(images, search_range, min_correlation_error, shift)
        # check that the shift has been changed
        assert_not_equals(shift, np.zeros((images.height, )))


if __name__ == '__main__':
    unittest.main()
