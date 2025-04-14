# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

# import io
# from pathlib import Path
# from unittest import mock

import unittest
import numpy as np
from parameterized import parameterized

from mantidimaging.core.data.geometry import Geometry
from mantidimaging.core.utility.data_containers import ScalarCoR


class GeometryTest(unittest.TestCase):

    def test_default_geometry(self):
        geo = Geometry()

        self.assertTrue(geo.is_parallel)
        self.assertTrue(np.array_equal(geo.config.system.ray.direction, np.array([0, 1, 0])))
        self.assertTrue(np.array_equal(geo.config.system.detector.position, np.array([0, 0, 0])))
        self.assertTrue(np.array_equal(geo.config.system.detector._direction_x, np.array([1, 0, 0])))
        self.assertTrue(np.array_equal(geo.config.system.detector._direction_y, np.array([0, 0, 1])))
        self.assertTrue(np.array_equal(geo.config.system.rotation_axis.position, np.array([0, 0, 0])))
        self.assertTrue(np.array_equal(geo.config.system.rotation_axis.direction, np.array([0, 0, 1])))
        self.assertEqual(geo.config.system.units, "default")

        self.assertTrue(np.array_equal(geo.config.panel.num_pixels, np.array((10, 10))))
        self.assertTrue(np.array_equal(geo.config.panel.pixel_size, np.array((1., 1.))))
        self.assertEqual(geo.config.panel.origin, "bottom-left")

        self.assertTrue(np.array_equal(geo.config.angles.angle_data, np.array(range(0, 180))))
        self.assertEqual(geo.config.angles.initial_angle, 0)
        self.assertEqual(geo.config.angles.angle_unit, "radian")
        self.assertEqual(geo.get_centre_of_rotation()["offset"], (0.0, "default"))
        self.assertEqual(geo.get_centre_of_rotation()["angle"], (0.0, "radian"))

    def test_set_geometry(self):
        num_pixels = (50, 50)
        pixel_size = (2, 2)

        geo = Geometry()
        new_geo = Geometry(num_pixels=num_pixels, pixel_size=pixel_size)
        geo.set_geometry(new_geo)

        self.assertTrue(geo.is_parallel)
        self.assertEqual(geo.config, new_geo.config)

    @parameterized.expand([("default_units", {
        "offset": (0.0, "default"),
        "angle": (0.0, "radian")
    }, {
        "offset": (0.0, "default"),
        "angle": (0.0, "radian")
    }),
                           ("positive_offset_angle", {
                               "offset": (10.0, "default"),
                               "angle": (1.0, "radian")
                           }, {
                               "offset": (10.0, "default"),
                               "angle": (1.0, "radian")
                           }),
                           ("negative_offset_angle", {
                               "offset": (-10.0, "default"),
                               "angle": (-1.0, "radian")
                           }, {
                               "offset": (-10.0, "default"),
                               "angle": (-1.0, "radian")
                           }),
                           ("pixel_distance_units", {
                               "offset": (10.0, "pixels"),
                               "angle": (0.0, "radian")
                           }, {
                               "offset": (10.0, "default"),
                               "angle": (0.0, "radian")
                           }),
                           ("degree_angle_units", {
                               "offset": (0.0, "default"),
                               "angle": (1.0, "degree")
                           }, {
                               "offset": (0.0, "default"),
                               "angle": (0.017453292519942303, "radian")
                           })])
    def test_set_cor(self, _, cor, expected_cor):
        """Tests setting the AcquisitionGeometry centre of rotation values. """
        num_pixels = (512, 512)
        pixel_size = (1, 1)

        geo = Geometry(num_pixels=num_pixels, pixel_size=pixel_size)
        geo.set_cor(cor)

        self.assertEqual(geo.get_centre_of_rotation()["offset"][0], expected_cor["offset"][0])
        self.assertTrue(np.isclose(geo.get_centre_of_rotation()["angle"][0], expected_cor["angle"][0]))
        self.assertEqual(geo.get_centre_of_rotation()["angle"][1], expected_cor["angle"][1])

    def test_set_cor_list(self):
        cor = {"offset": (10.0, "pixels"), "angle": (1.0, "degree")}
        cor_list = [cor] * 5

        geo = Geometry()
        geo.set_cor_list(cor_list)

        self.assertEqual(geo.cor_list, cor_list)

    @parameterized.expand([
        ("default_offset_angle", ScalarCoR(256.0), 0.0, {
            "offset": (0.0, "pixels"),
            "angle": (-0.0, "degree")
        }),
        ("positive_offset_angle", ScalarCoR(266.0), 1.0, {
            "offset": (10.0, "pixels"),
            "angle": (-1.0, "degree")
        }),
        ("negative_offset_angle", ScalarCoR(246.0), -1.0, {
            "offset": (-10.0, "pixels"),
            "angle": (1.0, "degree")
        }),
    ])
    def test_convert_cor_512(self, _, cor, tilt, expected_cil_cor):
        num_pixels = (512, 512)
        pixel_size = (1, 1)

        geo = Geometry(num_pixels=num_pixels, pixel_size=pixel_size)
        cil_cor = geo.convert_cor(cor, tilt)

        self.assertEqual(cil_cor, expected_cil_cor)

    @parameterized.expand([
        ("default_offset_angle", ScalarCoR(4.0), 0.0, {
            "offset": (0.0, "pixels"),
            "angle": (-0.0, "degree")
        }),
        ("positive_offset_angle", ScalarCoR(5.0), 1.0, {
            "offset": (1.0, "pixels"),
            "angle": (-1.0, "degree")
        }),
        ("negative_offset_angle", ScalarCoR(3.0), -1.0, {
            "offset": (-1.0, "pixels"),
            "angle": (1.0, "degree")
        }),
    ])
    def test_convert_cor_8(self, _, cor, tilt, expected_cil_cor):
        num_pixels = (8, 8)
        pixel_size = (1, 1)

        geo = Geometry(num_pixels=num_pixels, pixel_size=pixel_size)
        cil_cor = geo.convert_cor(cor, tilt)

        self.assertEqual(cil_cor, expected_cil_cor)

    @parameterized.expand([
        ("default_offset_angle", ScalarCoR(256.0), 0.0, {
            "offset": (0.0, "pixels"),
            "angle": (-0.0, "degree")
        }),
        ("positive_offset_angle", ScalarCoR(266.0), 1.0, {
            "offset": (10.0, "pixels"),
            "angle": (-1.0, "degree")
        }),
        ("negative_offset_angle", ScalarCoR(246.0), -1.0, {
            "offset": (-10.0, "pixels"),
            "angle": (1.0, "degree")
        }),
    ])
    def test_convert_cor_list(self, _, cor, tilt, expected_cil_cor):
        cor_list = [cor] * 512
        expected_cil_cor_list = [expected_cil_cor] * 512

        num_pixels = (512, 512)
        pixel_size = (1, 1)

        geo = Geometry(num_pixels=num_pixels, pixel_size=pixel_size)
        cil_cor_list = geo.convert_cor_list(cor_list, tilt)

        self.assertEqual(cil_cor_list, expected_cil_cor_list)
