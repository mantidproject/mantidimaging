# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

from unittest import mock

from mantidimaging.gui.dialogs.async_task import (AsyncTaskDialogView)
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class AsyncTaskDialogViewTest(unittest.TestCase):

    @mock.patch('mantidimaging.gui.dialogs.async_task.view.AsyncTaskDialogPresenter')
    def setUp(self, mock_atd) -> None:
        self.view = AsyncTaskDialogView(None)
        self.view.infoText = mock.Mock()
        self.mock_qtimer = mock.Mock()
        self.view.show_timer = self.mock_qtimer
        self.mock_atd = mock_atd

    def test_handle_completion_success(self):
        self.view.handle_completion(True)
        self.view.infoText.setText.assert_called_once_with("Complete")

    def test_handle_completion_fail(self):
        self.view.handle_completion(False)
        self.view.infoText.setText.assert_called_once_with("Task failed.")

    def test_show_delayed(self):
        self.view.show_delayed(10)

        self.mock_qtimer.singleShot.assert_called_once_with(10, self.view.show_from_timer)
        self.mock_qtimer.start.assert_called_once()
