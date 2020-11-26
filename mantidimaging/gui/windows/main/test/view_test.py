# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

from PyQt5.QtWidgets import QDialog

from mantidimaging.test_helpers import start_qapplication

from mantidimaging.gui.windows.main import MainWindowView


@start_qapplication
class MainWindowViewTest(unittest.TestCase):
    def setUp(self) -> None:
        with mock.patch("mantidimaging.gui.windows.main.view.check_version_and_label") as check_version_and_label:
            self.v = MainWindowView()
            self.p = mock.MagicMock()
            self.v.presenter = self.p
            self.check_version_and_label = check_version_and_label

    @mock.patch("mantidimaging.gui.windows.main.view.StackSelectorDialog")
    @mock.patch("mantidimaging.gui.windows.main.view.Qt.QFileDialog.getOpenFileName")
    def test_load_180_deg_dialog(self, get_open_file_name: mock.Mock, stack_selector_diag: mock.Mock):
        stack_selector_diag.return_value.exec.return_value = QDialog.Accepted
        selected_stack = "selected_stack"
        stack_selector_diag.return_value.selected_stack = selected_stack
        selected_file = "~/home/test/directory/selected_file.tif"
        get_open_file_name.return_value = (selected_file, None)
        _180_dataset = mock.MagicMock()
        self.p.add_180_deg_to_sample.return_value = _180_dataset
        self.v.create_new_stack = mock.MagicMock()
        selected_filename = "selected_file.tif"
        self.p.create_stack_name = mock.MagicMock(return_value=selected_filename)

        self.v.load_180_deg_dialog()

        stack_selector_diag.assert_called_once_with(main_window=self.v,
                                                    title='Stack Selector',
                                                    message='Which stack is the 180 degree projection being loaded '
                                                    'for?')
        get_open_file_name.assert_called_once_with(caption="180 Degree Image",
                                                   filter="Image File (*.tif *.tiff);;All (*.*)",
                                                   initialFilter="Image File (*.tif *.tiff)")
        self.p.add_180_deg_to_sample.assert_called_once_with(stack_name=selected_stack, _180_deg_file=selected_file)
        self.p.create_stack_name.assert_called_once_with(selected_file)
        self.v.create_new_stack.assert_called_once_with(_180_dataset, selected_filename)
