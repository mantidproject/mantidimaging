# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from unittest import mock

from mantidimaging.gui.windows.move_stack_dialog.presenter import MoveStackPresenter, Notification, DATASET_ATTRS
from mantidimaging.gui.windows.move_stack_dialog.view import MoveStackDialog


class MoveStackPresenterTest(unittest.TestCase):

    def setUp(self):
        self.view = mock.Mock(spec=MoveStackDialog)
        self.view.parent_view = mock.Mock()
        self.presenter = MoveStackPresenter(self.view)
        self.view.datasetSelector = mock.Mock()
        self.view.originDatasetName = mock.Mock()
        self.view.destinationTypeComboBox = mock.Mock()
        self.view.originDataType = mock.Mock()

    def test_on_accepted(self):
        self.view.origin_dataset_id = origin_dataset_id = "origin-dataset-id"
        self.view.stack_id = stack_id = "stack-id"
        self.view.destination_stack_type = destination_stack_type = "destination_stack_type"
        self.view.destination_dataset_id = destination_dataset_id = "destination-dataset-id"

        self.presenter.notify(Notification.ACCEPTED)
        self.view.parent_view.execute_move_stack.assert_called_once_with(origin_dataset_id, stack_id,
                                                                         destination_stack_type, destination_dataset_id)

    def test_notify_exception(self):
        self.presenter._on_accepted = mock.Mock(side_effect=RuntimeError)
        self.presenter.notify(Notification.ACCEPTED)
        self.view.show_error_dialog.assert_called_once()

    def test_destination_combo_box_when_moving_to_same_dataset(self):
        self.view.datasetSelector.current.return_value = self.view.origin_dataset_id = "dataset-id"
        self.view.originDataType.text.return_value = origin_data_type = "Flat Before"
        self.presenter.notify(Notification.DATASET_CHANGED)

        self.view.destinationTypeComboBox.clear.assert_called_once()
        type_list = DATASET_ATTRS.copy()
        type_list.remove(origin_data_type)
        self.view.destinationTypeComboBox.addItems.assert_called_once_with(type_list)

    def test_destination_combo_box_when_moving_to_different_dataset(self):
        self.view.datasetSelector.current.return_value = "dest-dataset-id"
        self.view.origin_dataset_id = "origin-dataset-id"
        self.presenter.notify(Notification.DATASET_CHANGED)

        self.view.destinationTypeComboBox.clear.assert_called_once()
        self.view.destinationTypeComboBox.addItems.assert_called_once_with(DATASET_ATTRS)
