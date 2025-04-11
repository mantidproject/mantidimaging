# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

# import io
# from pathlib import Path
# from unittest import mock

import unittest
import numpy as np
# from parameterized import parameterized

from mantidimaging.core.data.geometry import Geometry
# from mantidimaging.core.utility.data_containers import ScalarCoR


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
        self.assertEqual(geo.config.system.units, "units distance")

        self.assertTrue(np.array_equal(geo.config.panel.num_pixels, np.array((10, 10))))
        self.assertTrue(np.array_equal(geo.config.panel.pixel_size, np.array((1., 1.))))
        self.assertEqual(geo.config.panel.origin, "bottom-left")

        self.assertTrue(np.array_equal(geo.config.angles.angle_data, np.array(range(0, 180))))
        self.assertEqual(geo.config.angles.initial_angle, 0)
        self.assertEqual(geo.config.angles.angle_unit, "radian")
        self.assertEqual(geo.get_centre_of_rotation()["offset"], (0.0, "units distance"))
        self.assertEqual(geo.get_centre_of_rotation()["angle"], (0.0, "radian"))

    # @parameterized.expand([
    #     ("std_dev", ),
    #     ("std_dev", ErrorMode.PROPAGATED,
    #      [0.0000, 0.0772, 0.1306, 0.1823, 0.2335, 0.2845, 0.3354, 0.3862, 0.4369, 0.4876]),
    # ])
    def test_set_geometry(self):
        num_pixels = (50, 50)
        pixel_size = (2, 2)

        geo = Geometry()
        new_geo = Geometry(num_pixels=num_pixels, pixel_size=pixel_size)
        geo.set_geometry(new_geo)

        self.assertTrue(geo.is_parallel)
        self.assertEqual(geo.config, new_geo.config)

    def test_set_cor(self):
        cor = {"offset": (10.0, "pixels"), "angle": (1.0, "degree")}

        geo = Geometry()
        geo.set_cor(cor)

        self.assertEqual(geo.get_centre_of_rotation()["offset"], (10.0, "pixels"))
        self.assertEqual(geo.get_centre_of_rotation()["angle"], (1.0, "degree"))

    def test_set_cor_list(self):
        cor = {"offset": (10.0, "pixels"), "angle": (1.0, "degree")}
        cor_list = [cor] * 5

        geo = Geometry()
        geo.set_cor_list(cor_list)

        self.assertEqual(geo.cor_list, cor_list)
