# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

import numpy as np
from matplotlib.figure import Figure

from mantidimaging.core.data import ImageStack
from mantidimaging.gui.windows.geometry import GeometryWindowModel
from mantidimaging.test_helpers.unit_test_helper import generate_angles


class GeometryWindowModelTest(unittest.TestCase):

    def setUp(self):
        self.model = GeometryWindowModel()
        self.data = ImageStack(data=np.ndarray(shape=(10, 128, 256), dtype=np.float32))
        test_angles = generate_angles(360, self.data.num_projections)
        self.data.set_projection_angles(test_angles)

    def test_generate_figure(self):
        test_figure = self.model.generate_figure(self.data)
        self.assertIsInstance(test_figure, Figure)
