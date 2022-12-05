# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

from mantidimaging.gui.windows.move_stack_dialog.presenter import MoveStackPresenter, Notification
from mantidimaging.gui.windows.move_stack_dialog.view import MoveStackDialog


class MoveStackPresenterTest(unittest.TestCase):
    def setUp(self):
        self.view = mock.Mock(spec=MoveStackDialog)
        self.view.parent_view = mock.Mock()
        self.presenter = MoveStackPresenter(self.view)

    def test_on_accepted(self):
        self.view.origin_dataset_id = origin_dataset_id = "origin-dataset-id"
        self.view.stack_id = stack_id = "stack-id"
        self.view.destination_stack_type = destination_stack_type = "destination_stack_type"
        self.view.destination_dataset_name = destination_dataset_name = "destination-dataset-name"

        self.presenter.notify(Notification.ACCEPTED)
        self.view.parent_view.execute_move_stack.assert_called_once_with(origin_dataset_id, stack_id,
                                                                         destination_stack_type,
                                                                         destination_dataset_name)

    def test_notify_exception(self):
        self.presenter._on_accepted = mock.Mock(side_effect=RuntimeError)
        self.presenter.notify(Notification.ACCEPTED)
        self.view.show_error_dialog.assert_called_once()
