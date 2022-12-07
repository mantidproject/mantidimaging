# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

from mantidimaging.gui.windows.main import MainWindowView

from mantidimaging.gui.windows.move_stack_dialog.view import MoveStackDialog, STRICT_DATASET_ATTRS
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

        self.strict_dataset_name = "Strict Dataset"
        self.mixed_dataset_name = "Mixed Dataset"

        self.is_dataset_strict = {
            self.strict_dataset_name: True,
            self.mixed_dataset_name: False,
            self.origin_dataset_name: True
        }
        self.view = MoveStackDialog(self.main_window, self.origin_dataset_id, self.stack_id, self.origin_dataset_name,
                                    self.origin_data_type, self.is_dataset_strict)

    def test_combo_box_contains_dataset_names(self):
        assert self.view.destinationNameComboBox.count() == len(self.is_dataset_strict)
        index = 0
        for key in self.is_dataset_strict.keys():
            assert key == self.view.destinationNameComboBox.itemText(index)
            index += 1

    def test_destination_dataset_strict_options(self):
        """
        When the destination dataset is strict, the user should be able to have a stack moved to it become a Flat
        Before, Flat After, etc
        """
        self.view.destinationNameComboBox.setCurrentText(self.strict_dataset_name)
        destination_stack_type_options = [
            self.view.destinationTypeComboBox.itemText(i) for i in range(self.view.destinationTypeComboBox.count())
        ]
        self.assertListEqual(destination_stack_type_options, STRICT_DATASET_ATTRS)

    def test_destination_dataset_mixed_options(self):
        """
        When the dataset is mixed, the user should be able to have a stack moved to it become an Images stack or a recon
        only
        """
        self.view.destinationNameComboBox.setCurrentText(self.mixed_dataset_name)
        destination_stack_type_options = [
            self.view.destinationTypeComboBox.itemText(i) for i in range(self.view.destinationTypeComboBox.count())
        ]
        self.assertListEqual(destination_stack_type_options, ["Images", "Recon"])
