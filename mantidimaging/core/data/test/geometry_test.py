# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from math import degrees, atan

import unittest

import numpy as np
import numpy.testing as npt

from parameterized import parameterized

from mantidimaging.core.data.geometry import Geometry, GeometryType
from mantidimaging.core.utility.data_containers import ScalarCoR

TEST_ANGLES = np.array(range(0, 180))


class GeometryTest(unittest.TestCase):

    def test_default_geometry(self):
        """
        Tests the instantiation of a default Geometry object.
        """
        geo = Geometry(TEST_ANGLES)

        self.assertTrue(geo.type == GeometryType.PARALLEL3D)
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
        ("512x512",
         Geometry(TEST_ANGLES, num_pixels=(512, 512), pixel_size=(2., 2.), angle_unit="degree", units="pixels"), {
             "num_pixels": (512, 512),
             "pixel_size": (2., 2.),
             "angle_unit": "degree",
             "units": "pixels"
         }),
        ("8x8", Geometry(TEST_ANGLES, num_pixels=(8, 8), pixel_size=(4., 4.), angle_unit="degree", units="pixels"), {
            "num_pixels": (8, 8),
            "pixel_size": (4., 4.),
            "angle_unit": "degree",
            "units": "pixels"
        }),
        ("256x128",
         Geometry(TEST_ANGLES, num_pixels=(256, 128), pixel_size=(8., 4.), angle_unit="degree", units="pixels"), {
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

    @parameterized.expand([("default_units", ScalarCoR(5.0), 0.0), ("positive_offset_angle", ScalarCoR(6.0), 1.0),
                           ("negative_offset_angle", ScalarCoR(4.0), -1.0)])
    def test_set_geometry_from_cor_tilt_default(self, _, cor, tilt):
        """
        Tests converting and setting the AcquisitionGeometry centre of rotation value.
        """
        geo = Geometry(TEST_ANGLES)
        geo.set_geometry_from_cor_tilt(cor, tilt)

        self.assertEqual(geo.cor.value, cor.value)
        self.assertTrue(np.isclose(geo.tilt, tilt))

    @parameterized.expand([("default_units", ScalarCoR(256.0), 0.0), ("positive_offset_angle", ScalarCoR(266.0), 1.0),
                           ("negative_offset_angle", ScalarCoR(246.0), -1.0)])
    def test_set_geometry_from_cor_tilt_512(self, _, cor, tilt):
        """
        Tests converting a centre of rotation and tilt (MI convention) into offset/angle values (CIL convention).
        Defines a Geometry object's detector using the horizontal/vertical dimensions 512x512.
        """
        num_pixels = (512, 512)
        pixel_size = (1., 1.)

        geo = Geometry(TEST_ANGLES, num_pixels=num_pixels, pixel_size=pixel_size)
        geo.set_geometry_from_cor_tilt(cor, tilt)

        self.assertAlmostEqual(geo.cor.value, cor.value, delta=0.0001)
        self.assertTrue(np.isclose(geo.tilt, tilt))

    @parameterized.expand([("default_units", ScalarCoR(4.0), 0.0), ("positive_offset_angle", ScalarCoR(5.0), 1.0),
                           ("negative_offset_angle", ScalarCoR(3.0), -1.0)])
    def test_set_geometry_from_cor_tilt_8(self, _, cor, tilt):
        """
        Tests converting a centre of rotation and tilt (MI convention) into offset/angle values (CIL convention).
        Defines a Geometry object's detector using the horizontal/vertical dimensions 8x8.
        """
        num_pixels = (8, 8)
        pixel_size = (1., 1.)

        geo = Geometry(TEST_ANGLES, num_pixels=num_pixels, pixel_size=pixel_size)
        geo.set_geometry_from_cor_tilt(cor, tilt)

        self.assertEqual(geo.cor.value, cor.value)
        self.assertTrue(np.isclose(geo.tilt, tilt))

    @parameterized.expand([
        ("default_units", ScalarCoR(64), 0.0, 0.0),
        ("positive_offset_angle", ScalarCoR(64), degrees(atan(0.5)), -32),
        ("negative_offset_angle", ScalarCoR(64), -degrees(atan(0.5)), 32),
    ])
    def test_set_mi_cor_sets_cil_geometry_128(self, _, cor, tilt, expected_cil_offset):
        """
        Tests that setting the MI-convention COR/tilt values sets the correct internal CIL geometry.
        """

        num_pixels = (128, 128)
        pixel_size = (1., 1.)

        geo = Geometry(TEST_ANGLES, num_pixels=num_pixels, pixel_size=pixel_size)
        geo.set_geometry_from_cor_tilt(cor, tilt)

        cil_offset = geo.get_centre_of_rotation()['offset'][0]
        cil_angle = -degrees(geo.get_centre_of_rotation()['angle'][0])

        self.assertAlmostEqual(cil_offset, expected_cil_offset, places=6)
        self.assertAlmostEqual(cil_angle, tilt, places=6)

    @parameterized.expand([
        ("default_units", ScalarCoR(128), 0.0, 0.0),
        ("positive_offset_angle", ScalarCoR(128), degrees(atan(0.25)), -64),
        ("negative_offset_angle", ScalarCoR(128), -degrees(atan(0.25)), 64),
    ])
    def test_set_mi_cor_sets_cil_geometry_256_512(self, _, cor, tilt, expected_cil_offset):
        """
        Tests that setting the MI-convention COR/tilt values sets the correct internal CIL geometry for
        a non-square image.
        """

        num_pixels = (256, 512)
        pixel_size = (1., 1.)

        geo = Geometry(TEST_ANGLES, num_pixels=num_pixels, pixel_size=pixel_size)
        geo.set_geometry_from_cor_tilt(cor, tilt)

        cil_offset = geo.get_centre_of_rotation()['offset'][0]
        cil_angle = -degrees(geo.get_centre_of_rotation()['angle'][0])

        self.assertAlmostEqual(cil_offset, expected_cil_offset, places=6)
        self.assertAlmostEqual(cil_angle, tilt, places=6)

    def test_geometry_type(self):
        """
        Tests that the correct geometry type is returned.
        """
        num_pixels = (256, 512)
        pixel_size = (1., 1.)
        geo = Geometry(TEST_ANGLES, num_pixels=num_pixels, pixel_size=pixel_size)
        self.assertEqual(geo.type, GeometryType.PARALLEL3D)
