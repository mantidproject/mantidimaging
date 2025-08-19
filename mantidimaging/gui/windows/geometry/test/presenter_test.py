# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

from unittest import mock

import numpy
import numpy as np

from mantidimaging.core.data.geometry import GeometryType
from mantidimaging.core.utility.data_containers import ProjectionAngles

from mantidimaging.core.data import ImageStack
from mantidimaging.gui.windows.geometry import GeometryWindowPresenter, GeometryWindowView

TEST_PIXEL_SIZE = 1443


class GeometryWindowPresenterTest(unittest.TestCase):

    def setUp(self):
        self.data = ImageStack(data=np.ndarray(shape=(128, 10, 128), dtype=np.float32))
        self.uuid = self.data.id

        self.main_window = mock.MagicMock()
        self.main_window.get_stack.return_value = self.data

        self.make_view()
        self.presenter = GeometryWindowPresenter(view=self.view, main_window=self.main_window)

    def make_view(self):
        self.view = mock.create_autospec(GeometryWindowView, instance=True)
        self.view.type = "N/A"
        self.view.rotation_axis = 0
        self.view.tilt = 0
        self.view.new_rotation_axis = 0
        self.view.new_tilt = 0
        self.view.new_min_angle = 0
        self.view.new_max_angle = 0
        self.view.current_stack = self.uuid

    def reset_new_stack(self):
        self.data = ImageStack(data=np.ndarray(shape=(128, 10, 128), dtype=np.float32))

    def test_update_parameters(self):
        self.reset_new_stack()
        test_stack = self.main_window.get_stack()
        test_stack.set_projection_angles(ProjectionAngles(numpy.linspace(0, 360, test_stack.num_projections)))
        test_stack.set_geometry()
        self.presenter.update_parameters(test_stack)
        test_geometry_type = GeometryType.PARALLEL3D.value
        self.assertEqual(self.view.type, test_geometry_type)
        self.assertEqual(self.view.rotation_axis, test_stack.geometry.cor.value)
        self.assertEqual(self.view.tilt, test_stack.geometry.tilt)

    def test_create_geometry_button_creates_geometry(self):
        self.reset_new_stack()
        test_stack = self.main_window.get_stack()
        self.assertIsNone(test_stack.geometry)
        self.presenter.set_default_new_parameters(stack=test_stack)
        self.presenter.handle_create_new_geometry()
        self.assertIsNotNone(test_stack.geometry)

    def test_changing_cor_tilt_updates_geometry(self):
        self.presenter.handle_create_new_geometry()
        test_cor = 240
        test_tilt = 15
        self.view.rotation_axis = test_cor
        self.view.tilt = test_tilt
        self.presenter.handle_parameter_updates()
        self.assertAlmostEqual(self.data.geometry.cor.value, test_cor, places=10)
        self.assertAlmostEqual(self.data.geometry.tilt, test_tilt, places=10)
