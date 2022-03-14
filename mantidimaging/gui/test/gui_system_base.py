# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
from pathlib import Path
from typing import Callable, Optional
import unittest
from unittest import mock

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog
import pytest

from mantidimaging.core.utility.version_check import versions
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.load_dialog.presenter import Notification
from mantidimaging.test_helpers.start_qapplication import start_qapplication

versions._use_test_values()

LOAD_SAMPLE = str(Path.home()) + "/mantidimaging-data/ISIS/IMAT/IMAT00010675/Tomo/IMAT_Flower_Tomo_000000.tif"
LOAD_SAMPLE_MISSING_MESSAGE = """Data not present, please clone to your home directory e.g.
git clone https://github.com/mantidproject/mantidimaging-data.git"""

SHOW_DELAY = 10  # Can be increased to watch tests
SHORT_DELAY = 100


@pytest.mark.system
@unittest.skipUnless(os.path.exists(LOAD_SAMPLE), LOAD_SAMPLE_MISSING_MESSAGE)
@start_qapplication
class GuiSystemBase(unittest.TestCase):
    app: QApplication

    def setUp(self) -> None:
        self.main_window = MainWindowView()
        self.main_window.show()
        QTest.qWait(SHORT_DELAY)

    def tearDown(self) -> None:
        QTimer.singleShot(SHORT_DELAY, lambda: self._click_messageBox("Yes"))
        self.main_window.close()
        QTest.qWait(SHORT_DELAY)
        self.assertDictEqual(self.main_window.presenter.model.datasets, {})

    @classmethod
    def _click_messageBox(cls, button_text: str):
        """Needs to be queued with QTimer.singleShot before triggering the message box"""
        for widget in cls.app.topLevelWidgets():
            if isinstance(widget, QMessageBox) and widget.isVisible():
                for button in widget.buttons():
                    if button.text().replace("&", "") == button_text:
                        QTest.mouseClick(button, Qt.LeftButton)
                        return
                button_texts = [button.text() for button in widget.buttons()]
                raise ValueError(f"Could not find button '{button_text}' in {button_texts}.\n"
                                 f"Message box: {widget.windowTitle()} {widget.text()}")

    @classmethod
    def _click_InputDialog(cls, set_int: Optional[int] = None):
        """Needs to be queued with QTimer.singleShot before triggering the message box"""
        for widget in cls.app.topLevelWidgets():
            if isinstance(widget, QInputDialog) and widget.isVisible():
                if set_int:
                    widget.setIntValue(set_int)
                QTest.qWait(SHORT_DELAY)
                widget.accept()

    def _close_welcome(self):
        self.main_window.welcome_window.view.close()

    @classmethod
    def _wait_until(cls, test_func: Callable[[], bool], delay=0.1, max_retry=100):
        """
        Repeat test_func every delay seconds until is becomes true. Or if max_retry is reached return false.
        """
        for _ in range(max_retry):
            if test_func():
                return True
            QTest.qWait(int(delay * 1000))
        raise RuntimeError("_wait_until reach max retries")

    @classmethod
    def _wait_for_widget_visible(cls, widget_type, delay=0.1, max_retry=100):
        for _ in range(max_retry):
            for widget in cls.app.topLevelWidgets():
                if isinstance(widget, widget_type) and widget.isVisible():
                    return True
            QTest.qWait(delay * 1000)
        raise RuntimeError("_wait_for_stack_selector reach max retries")

    @mock.patch("mantidimaging.gui.windows.load_dialog.view.MWLoadDialog.select_file")
    def _load_data_set(self, mocked_select_file):
        mocked_select_file.return_value = LOAD_SAMPLE
        initial_stacks = len(self.main_window.presenter.get_active_stack_visualisers())

        def test_func() -> bool:
            current_stacks = len(self.main_window.presenter.get_active_stack_visualisers())
            return (current_stacks - initial_stacks) >= 5

        self.main_window.actionLoadDataset.trigger()
        QTest.qWait(SHOW_DELAY)
        self.main_window.load_dialogue.presenter.notify(Notification.UPDATE_ALL_FIELDS)
        QTest.qWait(SHOW_DELAY)
        self.main_window.load_dialogue.accept()
        self._wait_until(test_func, max_retry=600)

    def _open_operations(self):
        self.main_window.actionFilters.trigger()

    def _open_reconstruction(self):
        self.main_window.actionRecon.trigger()

    def _close_stack_tabs(self):
        while self.main_window.dataset_tree_widget.topLevelItemCount():
            self.main_window.dataset_tree_widget.topLevelItem(0).setSelected(True)
            self.main_window._delete_container()
