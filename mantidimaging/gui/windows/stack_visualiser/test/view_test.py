# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest

import mock
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDockWidget

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.data import Images
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class StackVisualiserViewTest(unittest.TestCase):
    test_data: Images

    def __init__(self, *args, **kwargs):
        super(StackVisualiserViewTest, self).__init__(*args, **kwargs)

    def tearDown(self) -> None:
        try:
            self.test_data.free_memory()
        except FileNotFoundError:
            pass

    def setUp(self):
        # mock the view so it has the same methods
        with mock.patch('mantidimaging.gui.windows.main.view.find_if_latest_version') as mock_find_latest_version:
            self.window = MainWindowView()
            mock_find_latest_version.assert_called_once()
        self.window.remove_stack = mock.Mock()
        self._add_stack_visualiser()

    def _add_stack_visualiser(self):
        self.dock = QDockWidget()
        self.dock.setWindowTitle("Potatoes")

        self.test_data = th.generate_images(automatic_free=False)
        self.view = StackVisualiserView(self.window, self.dock, self.test_data)
        self.dock.setWidget(self.view)
        self.window.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.dock)

    def test_name(self):
        title = "Potatoes"
        self.dock.setWindowTitle(title)
        self.assertEqual(title, self.view.name)

    def test_closeEvent_deletes_images(self):
        self.dock.setFloating = mock.Mock()
        self.dock.deleteLater = mock.Mock()

        self.view.close()

        self.dock.setFloating.assert_called_once_with(False)
        self.dock.deleteLater.assert_called_once_with()
        self.assertEqual(None, self.view.presenter.images)
        self.window.remove_stack.assert_called_once_with(self.view)

    def test_closeEvent_deletes_images_with_proj180(self):
        assert False, "TODO me"
        self._add_stack_visualiser()

        self.dock.setFloating = mock.Mock()
        self.dock.deleteLater = mock.Mock()

        self.view.close()

        self.dock.setFloating.assert_called_once_with(False)
        self.dock.deleteLater.assert_called_once_with()
        self.assertEqual(None, self.view.presenter.images)
        self.window.remove_stack.assert_called_once_with(self.view)

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
