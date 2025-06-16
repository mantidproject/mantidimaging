# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

import numpy as np
import numpy.testing as npt

from parameterized import parameterized

from mantidimaging.core.data.geometry import Geometry
from mantidimaging.core.utility.data_containers import ScalarCoR


class GeometryTest(unittest.TestCase):

    def test_default_geometry(self):
        """
        Tests the instantiation of a default Geometry object.
        """
        geo = Geometry()

        self.assertTrue(geo.is_parallel)
        npt.assert_array_equal(geo.config.system.ray.direction, np.array([0, 1, 0]))
        npt.assert_array_equal(geo.config.system.detector.position, np.array([0, 0, 0]))
        npt.assert_array_equal(geo.config.system.detector._direction_x, np.array([1, 0, 0]))
        npt.assert_array_equal(geo.config.system.detector._direction_y, np.array([0, 0, 1]))
        npt.assert_array_equal(geo.config.system.rotation_axis.position, np.array([0, 0, 0]))
        npt.assert_array_equal(geo.config.system.rotation_axis.direction, np.array([0, 0, 1]))
        self.assertEqual(geo.config.system.units, "default")

        npt.assert_array_equal(geo.config.panel.num_pixels, np.array((10, 10)))
        npt.assert_array_equal(geo.config.panel.pixel_size, np.array((1., 1.)))
        self.assertEqual(geo.config.panel.origin, "bottom-left")

        npt.assert_array_equal(geo.config.angles.angle_data, np.array(range(0, 180)))
        self.assertEqual(geo.config.angles.initial_angle, 0)
        self.assertEqual(geo.config.angles.angle_unit, "radian")
        self.assertEqual(geo.get_centre_of_rotation()["offset"], (0.0, "default"))
        self.assertEqual(geo.get_centre_of_rotation()["angle"], (0.0, "radian"))

    @parameterized.expand([
        ("512x512", Geometry(num_pixels=(512, 512), pixel_size=(2., 2.), angle_unit="degree", units="pixels"), {
            "num_pixels": (512, 512),
            "pixel_size": (2., 2.),
            "angle_unit": "degree",
            "units": "pixels"
        }),
        ("8x8", Geometry(num_pixels=(8, 8), pixel_size=(4., 4.), angle_unit="degree", units="pixels"), {
            "num_pixels": (8, 8),
            "pixel_size": (4., 4.),
            "angle_unit": "degree",
            "units": "pixels"
        }),
        ("256x128", Geometry(num_pixels=(256, 128), pixel_size=(8., 4.), angle_unit="degree", units="pixels"), {
            "num_pixels": (256, 128),
            "pixel_size": (8., 4.),
            "angle_unit": "degree",
            "units": "pixels"
        }),
    ])
    def test_custom_geometry(self, _, geo, expected_values):
        """
        Tests the instantiation of a custom Geometry object.
        """
        npt.assert_array_equal(geo.config.panel.num_pixels, np.array(expected_values["num_pixels"]))
        npt.assert_array_equal(geo.config.panel.pixel_size, np.array(expected_values["pixel_size"]))
        self.assertEqual(geo.config.angles.angle_unit, expected_values["angle_unit"])
        self.assertEqual(geo.config.system.units, expected_values["units"])

    @parameterized.expand([("default_units", ScalarCoR(5.0), 0.0, 0.0, 0.0),
                           ("positive_offset_angle", ScalarCoR(6.0), 1.0, 1.0, -1.0),
                           ("negative_offset_angle", ScalarCoR(4.0), -1.0, -1.0, 1.0)])
    def test_set_geometry_from_cor_tilt_default(self, _, cor, tilt, expected_offset, expected_angle):
        """
        Tests converting and setting the AcquisitionGeometry centre of rotation value.
        """
        geo = Geometry()
        geo.set_geometry_from_cor_tilt(cor, tilt)

        self.assertEqual(geo.get_centre_of_rotation()["offset"][0], expected_offset)
        self.assertTrue(np.isclose(geo.get_centre_of_rotation(angle_units='degree')["angle"][0], expected_angle))

    @parameterized.expand([("default_units", ScalarCoR(256.0), 0.0, 0.0, 0.0),
                           ("positive_offset_angle", ScalarCoR(266.0), 1.0, 10.0, -1.0),
                           ("negative_offset_angle", ScalarCoR(246.0), -1.0, -10.0, 1.0)])
    def test_set_geometry_from_cor_tilt_512(self, _, cor, tilt, expected_offset, expected_angle):
        """
        Tests converting a centre of rotation and tilt (MI convention) into offset/angle values (CIL convention).
        Defines a Geometry object's detector using the horizontal/vertical dimensions 512x512.
        """
        num_pixels = (512, 512)
        pixel_size = (1., 1.)

        geo = Geometry(num_pixels=num_pixels, pixel_size=pixel_size)
        geo.set_geometry_from_cor_tilt(cor, tilt)

        self.assertEqual(geo.get_centre_of_rotation()["offset"][0], expected_offset)
        self.assertTrue(np.isclose(geo.get_centre_of_rotation(angle_units='degree')["angle"][0], expected_angle))

    @parameterized.expand([("default_units", ScalarCoR(4.0), 0.0, 0.0, 0.0),
                           ("positive_offset_angle", ScalarCoR(5.0), 1.0, 1.0, -1.0),
                           ("negative_offset_angle", ScalarCoR(3.0), -1.0, -1.0, 1.0)])
    def test_set_geometry_from_cor_tilt_8(self, _, cor, tilt, expected_offset, expected_angle):
        """
        Tests converting a centre of rotation and tilt (MI convention) into offset/angle values (CIL convention).
        Defines a Geometry object's detector using the horizontal/vertical dimensions 8x8.
        """
        num_pixels = (8, 8)
        pixel_size = (1., 1.)

        geo = Geometry(num_pixels=num_pixels, pixel_size=pixel_size)
        geo.set_geometry_from_cor_tilt(cor, tilt)

        self.assertEqual(geo.get_centre_of_rotation()["offset"][0], expected_offset)
        self.assertTrue(np.isclose(geo.get_centre_of_rotation(angle_units='degree')["angle"][0], expected_angle))
