# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
import uuid
from unittest import mock

from mantidimaging.core.data import ImageStack
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.stack_rename_dialog.presenter import Notification

from mantidimaging.gui.windows.stack_rename_dialog.view import StackRenameDialog
from mantidimaging.test_helpers import start_qapplication

@start_qapplication
class StackRenameDialogTest(unittest.TestCase):

    def setUp(self) -> None:
        with mock.patch("mantidimaging.gui.windows.main.view.MainWindowView.show_welcome_screen"):
            self.main_window = MainWindowView()
        self.origin_stack = mock.Mock(spec=ImageStack)
        self.origin_stack.name = "stack_name"
        self.origin_stack.id = "stack_id"

        self.view = StackRenameDialog(self.main_window, self.origin_stack)
        self.view.presenter = self.presenter = mock.Mock()

    def test_accept(self):
        self.view.close = mock.Mock()
        self.view.accept()
        self.presenter.notify.assert_called_once_with(Notification.ACCEPTED)
        self.view.close.assert_called_once()

    def test_origin_stack_information_matched(self):
        self.assertEqual(self.origin_stack.name, self.view.stack_name)
        self.assertEqual(self.origin_stack.id, self.view.stack_id)

