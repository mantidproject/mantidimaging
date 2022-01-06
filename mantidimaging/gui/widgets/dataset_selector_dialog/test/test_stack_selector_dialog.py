# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

from PyQt5.QtWidgets import QWidget, QDialog

from mantidimaging.gui.widgets.stack_selector_dialog.stack_selector_dialog import StackSelectorDialog
from mantidimaging.test_helpers import start_qapplication


class FakeMainWindowView(QWidget):
    def __init__(self):
        super().__init__()
        self.model_changed = mock.MagicMock()


@start_qapplication
class StackSelectorDialogTest(unittest.TestCase):
    def test_message_label_set_to_given_message(self):
        given_message = "given_message"

        diag = StackSelectorDialog(main_window=FakeMainWindowView(), message=given_message)

        self.assertEqual(given_message, diag.message_label.text())

    def test_message_label_set_to_default_given_none(self):
        diag = StackSelectorDialog(main_window=FakeMainWindowView(), message=None)

        self.assertEqual("Select the stack", diag.message_label.text())

    def test_title_set_when_not_none_given(self):
        given_message = "given_message"

        diag = StackSelectorDialog(main_window=FakeMainWindowView(), title=given_message)

        self.assertEqual(given_message, diag.windowTitle())

    def test_title_not_set_when_none_given(self):
        diag = StackSelectorDialog(main_window=FakeMainWindowView(), title=None)

        self.assertEqual("", diag.windowTitle())

    def test_selected_stack_called_on_ok_clicked(self):
        diag = StackSelectorDialog(main_window=FakeMainWindowView())
        desired_stack = "Desired_stack"
        diag.stack_selector_widget.currentText = mock.MagicMock(return_value=desired_stack)

        diag.on_ok_clicked()

        self.assertEqual(desired_stack, diag.selected_stack)
        diag.stack_selector_widget.currentText.assert_called_once()

    def test_close_called_on_ok_clicked(self):
        diag = StackSelectorDialog(main_window=FakeMainWindowView())
        diag.done = mock.MagicMock()

        diag.on_ok_clicked()

        diag.done.assert_called_once_with(QDialog.DialogCode.Accepted)
