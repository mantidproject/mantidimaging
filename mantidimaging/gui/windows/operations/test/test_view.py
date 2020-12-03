# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.operations.view import FiltersWindowView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class OperationsWindowsViewTest(unittest.TestCase):
    def setUp(self):
        # mock the view so it has the same methods
        with mock.patch('mantidimaging.gui.windows.main.view.check_version_and_label'):
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
