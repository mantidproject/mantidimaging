# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from unittest import mock

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView
from mantidimaging.test_helpers import start_qapplication, mock_versions


@mock_versions
@start_qapplication
class StackVisualiserViewTest(unittest.TestCase):
    test_data: ImageStack
    window: MainWindowView

    def setUp(self):
        with mock.patch("mantidimaging.gui.windows.main.view.MainWindowView.show_welcome_screen"):
            self.window = MainWindowView()
        self.view, self.test_data = self._add_stack_visualiser()

    def _add_stack_visualiser(self) -> tuple[StackVisualiserView, ImageStack]:
        test_data = th.generate_images()
        test_data.name = "Test Data"
        self.window.create_new_stack(test_data)
        view = self.window.get_stack_with_images(test_data)
        return view, test_data

    def test_name(self):
        title = "Potatoes"
        self.view.setWindowTitle(title)
        self.assertEqual(title, self.view.name)

    def _roi_updated_callback(self, roi):
        self.assertIsInstance(roi, SensibleROI)

        self.assertEqual(roi.left, 1)
        self.assertEqual(roi.top, 2)
        self.assertEqual(roi.right, 3)
        self.assertEqual(roi.bottom, 4)

        self.roi_callback_was_called = True

    def test_roi_changed_callback(self):
        self.roi_callback_was_called = False
        self.view.roi_updated.connect(self._roi_updated_callback)

        self.view.roi_changed_callback(SensibleROI(1, 2, 3, 4))

        self.assertTrue(self.roi_callback_was_called)


if __name__ == '__main__':
    unittest.main()
