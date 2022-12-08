# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
import uuid
from unittest import mock

from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.move_stack_dialog.presenter import Notification

from mantidimaging.gui.windows.move_stack_dialog.view import MoveStackDialog, STRICT_DATASET_ATTRS
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class MoveStackDialogTest(unittest.TestCase):
    def setUp(self) -> None:
        with mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter"):
            self.main_window = MainWindowView()
        self.origin_dataset_id = uuid.uuid4()
        self.stack_id = uuid.uuid4()
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
        self.view.presenter = self.presenter = mock.Mock()

    def test_origin_stack_information_matched(self):
        assert self.origin_dataset_name == self.view.originDatasetName.text()
        assert self.origin_data_type == self.view.originDataType.text()

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

    def test_moved_stack_within_dataset_options(self):
        """
        When a stack is moved to the same dataset, it should not be possible to move it to the same data type
        (i.e. a Flat Before can become a Recon but moving it to Flat Before should not be possible)
        """
        self.view.destinationNameComboBox.setCurrentText(self.origin_dataset_name)
        destination_stack_type_options = [
            self.view.destinationTypeComboBox.itemText(i) for i in range(self.view.destinationTypeComboBox.count())
        ]
        self.assertNotIn(self.origin_data_type, destination_stack_type_options)

    def test_accept(self):
        self.view.close = mock.Mock()
        self.view.accept()
        self.presenter.notify.assert_called_once_with(Notification.ACCEPTED)
        self.view.close.assert_called_once()

    def test_origin_dataset_id(self):
        assert self.view.origin_dataset_id == self.origin_dataset_id

    def test_stack_id(self):
        assert self.view.stack_id == self.stack_id

    def test_destination_stack_type(self):
        self.view.destinationNameComboBox.setCurrentText(self.strict_dataset_name)
        assert self.view.destination_dataset_name == self.strict_dataset_name
