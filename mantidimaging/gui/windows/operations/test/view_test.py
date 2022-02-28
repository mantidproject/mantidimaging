# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.operations.view import FiltersWindowView
from mantidimaging.test_helpers import start_qapplication

from mantidimaging.core.utility.version_check import versions

versions._use_test_values()


@start_qapplication
class OperationsWindowsViewTest(unittest.TestCase):
    def setUp(self):
        # mock the view so it has the same methods
        with mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter"):
            self.main_window = MainWindowView()
        self.window = FiltersWindowView(self.main_window)

    def test_collapse(self):
        self.assertEqual("<<", self.window.collapseToggleButton.text())
        # check that left column is not 0
        self.assertNotEqual(0, self.window.splitter.sizes()[0])

        self.window.collapseToggleButton.click()

        self.assertEqual(">>", self.window.collapseToggleButton.text())
        # check that left column is 0 as expected as it has been collapsed
        self.assertEqual(0, self.window.splitter.sizes()[0])

    def test_on_auto_update_triggered_with_auto_selected(self):
        self.window.previewAutoUpdate = mock.Mock()
        self.window.previewAutoUpdate.isChecked.return_value = True
        self.window.isVisible = mock.Mock()
        self.window.isVisible.return_value = True

        with mock.patch("mantidimaging.gui.windows.operations.presenter.FiltersWindowPresenter.do_update_previews")\
                as mock_do_update_previews:
            self.window.on_auto_update_triggered()
            mock_do_update_previews.assert_called_once()

    def test_on_auto_update_triggered_with_auto_not_selected(self):
        self.window.previewAutoUpdate = mock.Mock()
        self.window.previewAutoUpdate.isChecked.return_value = False
        self.window.isVisible = mock.Mock()
        self.window.isVisible.return_value = True

        with mock.patch("mantidimaging.gui.windows.operations.presenter.FiltersWindowPresenter.do_update_previews")\
                as mock_do_update_previews:
            self.window.on_auto_update_triggered()
            mock_do_update_previews.assert_not_called()
