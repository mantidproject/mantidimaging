# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from unittest import mock

from mantidimaging.core.data import ImageStack
from mantidimaging.gui.windows.stack_rename_dialog.presenter import StackRenamePresenter, Notification
from mantidimaging.gui.windows.stack_rename_dialog.view import StackRenameDialog


class StackDialogPresenterTest(unittest.TestCase):

    def setUp(self):
        self.view = mock.Mock(spec=StackRenameDialog)
        self.view.parent_view = mock.Mock()
        self.presenter = StackRenamePresenter(self.view)

    def test_on_accepted(self):
        self.view.stack = mock.Mock(spec=ImageStack)
        self.view.new_name_field = mock.Mock()
        self.view.new_name_field.text = mock.Mock(return_value="new_name")

        self.presenter.notify(Notification.ACCEPTED)
        self.view.parent_view.execute_rename_dataset.assert_called_once_with(self.view.stack, "new_name")

    def test_notify_exception(self):
        self.presenter._on_accepted = mock.Mock(side_effect=RuntimeError)
        self.presenter.notify(Notification.ACCEPTED)
        self.view.show_error_dialog.assert_called_once()
