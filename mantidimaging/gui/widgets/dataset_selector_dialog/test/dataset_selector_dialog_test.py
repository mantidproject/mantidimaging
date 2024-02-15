# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

from PyQt5.QtWidgets import QWidget, QDialog

from mantidimaging.gui.widgets.dataset_selector_dialog.dataset_selector_dialog import DatasetSelectorDialog
from mantidimaging.test_helpers import start_qapplication


class FakeMainWindowView(QWidget):

    def __init__(self):
        super().__init__()
        self.model_changed = mock.MagicMock()


@start_qapplication
class DatasetSelectorDialogTest(unittest.TestCase):

    def test_title_set_when_not_none_given(self):
        given_message = "given_message"
        diag = DatasetSelectorDialog(main_window=FakeMainWindowView(), title=given_message)
        self.assertEqual(given_message, diag.windowTitle())

    def test_title_not_set_when_none_given(self):
        diag = DatasetSelectorDialog(main_window=FakeMainWindowView(), title=None)
        self.assertEqual("", diag.windowTitle())

    def test_message_label_set_to_given_message(self):
        given_message = "given_message"

        diag = DatasetSelectorDialog(main_window=FakeMainWindowView(), message=given_message)

        self.assertEqual(given_message, diag.message_label.text())

    def test_message_label_set_to_default_given_none(self):
        diag = DatasetSelectorDialog(main_window=FakeMainWindowView(), message=None)

        self.assertEqual("Select the dataset", diag.message_label.text())

    def test_selected_dataset_called_on_ok_clicked(self):
        diag = DatasetSelectorDialog(main_window=FakeMainWindowView())
        dataset_id = "dataset-id"
        diag.dataset_selector_widget.current = mock.MagicMock(return_value=dataset_id)

        diag.on_ok_clicked()

        self.assertEqual(dataset_id, diag.selected_id)
        diag.dataset_selector_widget.current.assert_called_once()

    def test_close_called_on_ok_clicked(self):
        diag = DatasetSelectorDialog(main_window=FakeMainWindowView())
        diag.done = mock.MagicMock()
        diag.on_ok_clicked()
        diag.done.assert_called_once_with(QDialog.DialogCode.Accepted)
