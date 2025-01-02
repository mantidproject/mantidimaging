# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

from PyQt5.QtWidgets import QMainWindow
from parameterized import parameterized

from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.widgets.roi_selector.view import ROISelectorView
from mantidimaging.test_helpers import start_qapplication
from mantidimaging.test_helpers.unit_test_helper import generate_images


@start_qapplication
class ROISelectorViewTest(unittest.TestCase):

    def setUp(self) -> None:
        self.parent = QMainWindow()
        self.image_stack = generate_images()
        self.slice_idx = 0

    def test_toggle_average_images(self):
        view = ROISelectorView(self.parent, self.image_stack, self.slice_idx)
        view.roi_view.setImage = mock.Mock()

        self.assertTrue(view.roi_view_averaged)
        view.toggle_average_images()
        self.assertFalse(view.roi_view_averaged)
        view.roi_view.setImage.assert_called_with(view.main_image)
        view.toggle_average_images()
        self.assertTrue(view.roi_view_averaged)
        view.roi_view.setImage.assert_called_with(view.averaged_image)

    @parameterized.expand([("Too_few", [1, 2, 10]), ("Too_many", [1, 2, 10, 20, 30]), ("None", None), ("Empty", [])])
    def test_invalid_roi_values_use_default(self, _, roi_values):
        view = ROISelectorView(self.parent, self.image_stack, self.slice_idx, roi_values)
        self._check_roi_set_correctly(view, view.roi_view.default_roi())

    def test_roi_values_set_correctly(self):
        roi_values = [1, 2, 10, 30]
        view = ROISelectorView(self.parent, self.image_stack, self.slice_idx, roi_values)
        self._check_roi_set_correctly(view, roi_values)

    def _check_roi_set_correctly(self, view, roi_values):
        roi = SensibleROI.from_list(roi_values)
        position = view.roi_view.roi.pos()
        size = view.roi_view.roi.size()

        self.assertEqual(roi.left, position[0])
        self.assertEqual(roi.top, position[1])
        self.assertEqual(roi.width, size[0])
        self.assertEqual(roi.height, size[1])
