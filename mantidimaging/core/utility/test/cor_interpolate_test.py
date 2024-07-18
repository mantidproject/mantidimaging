# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
import numpy as np
from numpy.testing import assert_array_almost_equal
from mantidimaging.core.utility.cor_interpolate import execute


class TestExecuteFunction(unittest.TestCase):

    def test_cor_interpolation(self):
        data_length = 20
        slice_ids = [0, 5, 15]
        cors_for_sinograms = [1.0, 5.0, 3.0]
        expected_output = np.interp(list(range(data_length)), slice_ids, cors_for_sinograms)
        result = execute(data_length, slice_ids, cors_for_sinograms)
        assert_array_almost_equal(result, expected_output)

    def test_empty_inputs(self):
        data_length = 5
        with self.assertRaises(AssertionError):
            execute(data_length, [], [2.5])

    def test_invalid_cor(self):
        data_length = 5
        slice_ids = [0, 1]
        cors_for_sinograms = [2.5, "3.0"]  # invalid type
        with self.assertRaises(AssertionError):
            execute(data_length, slice_ids, cors_for_sinograms)

    def test_invalid_slice_id(self):
        data_length = 5
        slice_ids = [0, "1"]  # invalid type
        cors_for_sinograms = [2.5, 3.0]
        with self.assertRaises(AssertionError):
            execute(data_length, slice_ids, cors_for_sinograms)


if __name__ == '__main__':
    unittest.main()
