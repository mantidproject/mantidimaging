# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
import uuid
from unittest import mock

from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.move_stack_dialog.presenter import Notification

from mantidimaging.gui.windows.move_stack_dialog.view import MoveStackDialog
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

        self.view = MoveStackDialog(self.main_window, self.origin_dataset_id, self.stack_id, self.origin_dataset_name,
                                    self.origin_data_type)
        self.view.presenter = self.presenter = mock.Mock()
        self.view.dataset_selector = self.dataset_selector = mock.Mock()

    def test_origin_stack_information_matched(self):
        self.assertEqual(self.origin_dataset_name, self.view.originDatasetName.text())
        self.assertEqual(self.origin_data_type, self.view.originDataType.text())

    def test_accept(self):
        self.view.close = mock.Mock()
        self.view.accept()
        self.presenter.notify.assert_called_once_with(Notification.ACCEPTED)
        self.view.close.assert_called_once()

    def test_on_destination_dataset_changed(self):
        self.view._on_destination_dataset_changed()
        self.presenter.notify.assert_called_once_with(Notification.DATASET_CHANGED)

    def test_origin_dataset_id(self):
        self.assertEqual(self.view.origin_dataset_id, self.origin_dataset_id)

    def test_stack_id(self):
        self.assertEqual(self.view.stack_id, self.stack_id)
