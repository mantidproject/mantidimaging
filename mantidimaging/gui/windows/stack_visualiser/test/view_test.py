# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import Tuple
import unittest

import mock
from PyQt5.QtWidgets import QDockWidget
from mock import Mock

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.data import Images
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class StackVisualiserViewTest(unittest.TestCase):
    test_data: Images
    window: MainWindowView

    def __init__(self, *args, **kwargs):
        super(StackVisualiserViewTest, self).__init__(*args, **kwargs)

    def tearDown(self) -> None:
        try:
            self.test_data.free_memory()
        except FileNotFoundError:
            pass
        self.view = None
        self.window = None  # type: ignore[assignment]
        self.dock = None

    def setUp(self):
        # mock the view so it has the same methods
        with mock.patch('mantidimaging.gui.windows.main.view.check_version_and_label') as mock_find_latest_version:
            with mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter"):
                self.window = MainWindowView()
            mock_find_latest_version.assert_called_once()
        self.window.remove_stack = mock.Mock()
        self.dock, self.view, self.test_data = self._add_stack_visualiser()

    def _add_stack_visualiser(self) -> Tuple[QDockWidget, StackVisualiserView, Images]:
        test_data = th.generate_images(automatic_free=False)
        self.window.create_new_stack(test_data, "Test Data")
        view = self.window.get_stack_with_images(test_data)
        return view.dock, view, test_data

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

    @mock.patch("mantidimaging.gui.windows.main.view.StackVisualiserView.ask_confirmation", return_value=True)
    def test_closeEvent_deletes_images_with_proj180_user_accepts(self, ask_confirmation_mock: Mock):
        p180_dock, p180_view, images = self._add_stack_visualiser()
        self.test_data.proj180deg = images

        p180_dock.setFloating = mock.Mock()  # type: ignore[assignment]
        p180_dock.deleteLater = mock.Mock()  # type: ignore[assignment]

        p180_view.close()

        ask_confirmation_mock.assert_called_once()

        # proj180 has been cleared from the stack referencing it
        self.assertFalse(self.test_data.has_proj180deg())

        p180_dock.setFloating.assert_called_once_with(False)
        p180_dock.deleteLater.assert_called_once_with()
        self.assertIsNone(p180_view.presenter.images)
        self.window.remove_stack.assert_called_once_with(p180_view)  # type: ignore[attr-defined]

    @mock.patch("mantidimaging.gui.windows.main.view.StackVisualiserView.ask_confirmation", return_value=False)
    def test_closeEvent_deletes_images_with_proj180_user_declined(self, ask_confirmation_mock: Mock):
        p180_dock, p180_view, images = self._add_stack_visualiser()
        self.test_data.proj180deg = images

        p180_dock.setFloating = mock.Mock()  # type: ignore[assignment]
        p180_dock.deleteLater = mock.Mock()  # type: ignore[assignment]

        p180_view.close()

        ask_confirmation_mock.assert_called_once()

        # proj180 has been cleared from the stack referencing it
        self.assertTrue(self.test_data.has_proj180deg())

        p180_dock.setFloating.assert_not_called()
        p180_dock.deleteLater.assert_not_called()
        self.assertIsNotNone(p180_view.presenter.images)
        self.window.remove_stack.assert_not_called()  # type: ignore[attr-defined]

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
