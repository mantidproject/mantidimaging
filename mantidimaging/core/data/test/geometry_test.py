# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

# import io
# from pathlib import Path
# from unittest import mock

import unittest

# import numpy as np

from mantidimaging.core.data.geometry import Geometry
# from mantidimaging.core.utility.data_containers import ScalarCoR


class GeometryTest(unittest.TestCase):

    def test_default_geometry(self):
        geo = Geometry()

        self.assertTrue(geo.is_parallel)
        # self.assertEqual(geo.config.system.ray_direction, [0, 1, 0])
        # self.assertEqual(geo.config.system.detector_position, [0, 0, 0])
        # self.assertEqual(geo.config.system.detector_direction_x, [1, 0, 0])
        # self.assertEqual(geo.config.system.detector_direction_y, [0, 0, 1])
        # self.assertEqual(geo.config.system.rotation_axis_direction, [0, 0, 0])
        # self.assertEqual(geo.config.system.units, "units distance")

        # self.assertEqual(geo.config.panel.num_pixels, (10, 10))
        # self.assertEqual(geo.config.panel.pixel_size, (1., 1.))
        # self.assertEqual(geo.config.angles.angles, range(0, 180))
        # self.assertEqual(geo.get_centre_of_rotation["offset"], 64)

    # def test_convert_cor(self):
    #     geo = Geometry()
    #     cor = ScalarCoR(256.0)
    #     tilt = 0.0

    # self.assertEqual(geo.convert_cor(cor, tilt), {"offset": (0.0, "units distance"), "angle": (0.0, "radian")})
