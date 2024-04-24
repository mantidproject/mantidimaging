# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np

import unittest
from numpy.testing import assert_array_almost_equal, assert_array_equal

from mantidimaging.core.utility import unit_conversion


class UnitConversionTest(unittest.TestCase):

    def setUp(self):
        self.tof_data = np.array([1, 2, 3, 5, 8, 9])

    def test_WHEN_no_data_THEN_error_on_check_data(self):
        self.assertRaises(TypeError, unit_conversion.UnitConversion().check_data)

    def test_WHEN_data_THEN_velocity_calculated(self):
        assert_array_almost_equal(
            unit_conversion.UnitConversion(self.tof_data).velocity,
            np.array([56., 28., 18.66666667, 11.2, 7., 6.22222222]))

    def test_WHEN_set_data_to_convert_THEN_data_set(self):
        units = unit_conversion.UnitConversion()
        units.set_data_to_convert(self.tof_data)
        assert_array_equal(units.tof_data_to_convert, self.tof_data)

    def test_WHEN_set_target_to_camera_dist_THEN_camera_dist_set(self):
        units = unit_conversion.UnitConversion()
        units.target_to_camera_dist = 30
        self.assertEqual(units.target_to_camera_dist, 30)

    def test_WHEN_set_data_offset_THEN_data_offset_set(self):
        units = unit_conversion.UnitConversion()
        units.set_data_offset(100)
        self.assertEqual(units.data_offset, 100 * 1e-6)

    def test_WHEN_tof_converted_to_wavelength_THEN_wavelength_data_returned(self):
        wavelength_data = unit_conversion.UnitConversion(self.tof_data).tof_seconds_to_wavelength_in_angstroms()
        assert_array_almost_equal(
            wavelength_data,
            np.array([70.64346392, 141.28692784, 211.93039176, 353.2173196, 565.14771137, 635.79117529]))

    def test_WHEN_tof_converted_to_energy_THEN_energy_data_returned(self):
        energy_data = unit_conversion.UnitConversion(self.tof_data).tof_seconds_to_energy()
        assert_array_almost_equal(energy_data,
                                  np.array([0.29271406, 0.14635703, 0.09757135, 0.05854281, 0.03658926, 0.03252378]))

    def test_WHEN_tof_converted_to_us_THEN_us_data_returned(self):
        us_data = unit_conversion.UnitConversion(self.tof_data).tof_seconds_to_us()
        assert_array_almost_equal(us_data, np.array([1000000., 2000000., 3000000., 5000000., 8000000., 9000000.]))
