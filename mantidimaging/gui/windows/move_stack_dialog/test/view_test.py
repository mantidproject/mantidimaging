# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

from mantidimaging.gui.windows.main import MainWindowView

from mantidimaging.gui.windows.move_stack_dialog.view import MoveStackDialog
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class MoveStackDialogTest(unittest.TestCase):
    def setUp(self) -> None:
        with mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter"):
            self.main_window = MainWindowView()
        self.origin_dataset_id = "origin-dataset-id"
        self.stack_id = "stack-id"
        self.origin_dataset_name = "Origin Dataset"
        self.origin_data_type = "Flat Before"
        self.is_dataset_strict = {"Dataset-1": True, "Dataset-2": False, self.origin_dataset_name: True}
        self.view = MoveStackDialog(self.main_window, self.origin_dataset_id, self.stack_id, self.origin_dataset_name,
                                    self.origin_data_type, self.is_dataset_strict)

    def test_combo_box_contains_dataset_names(self):
        assert self.view.destinationNameComboBox.count() == len(self.is_dataset_strict)
        index = 0
        for key in self.is_dataset_strict.keys():
            assert key == self.view.destinationNameComboBox.itemText(index)
            index += 1
