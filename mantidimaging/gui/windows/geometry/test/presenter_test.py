# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

from unittest import mock

import numpy as np

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
        self.view.rotation_axis = 0
        self.view.tilt = 0
        self.view.new_rotation_axis = 0
        self.view.new_tilt = 0
        self.view.new_min_angle = 0
        self.view.new_max_angle = 0
        self.view.current_stack = self.uuid

    def reset_new_stack(self):
        self.data = ImageStack(data=np.ndarray(shape=(128, 10, 128), dtype=np.float32))

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
        self.assertNotEqual(self.data.geometry.cor.value, 0)
        self.assertNotEqual(self.data.geometry.tilt, 0)
        self.assertAlmostEqual(self.data.geometry.cor.value, test_cor, places=10)
        self.assertAlmostEqual(self.data.geometry.tilt, test_tilt, places=10)
