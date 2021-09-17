# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

from mantidimaging.core.utility.command_line_arguments import filter_names
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

    def test_set_initial_operation(self):
        mixed_inputs = filter_names + [filter_name.upper() for filter_name in filter_names]
        for filter_name in mixed_inputs:
            with self.subTest(filter_name=filter_name):
                self.window.set_initial_filter(filter_name)
                self.assertEqual(
                    filter_name.replace(" ", "").replace("-", "").lower(),
                    self.window.filterSelector.currentText().replace(" ", "").replace("-", "").lower())
