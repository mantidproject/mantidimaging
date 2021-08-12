# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
from pathlib import Path
import sys
import unittest
from unittest import mock

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox
import pytest

from mantidimaging.core.utility.version_check import versions
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.load_dialog.presenter import Notification

versions._use_test_values()

LOAD_SAMPLE = str(Path.home()) + "/mantidimaging-data-master/ISIS/IMAT/IMAT00010675/Tomo/IMAT_Flower_Tomo_000000.tif"
LOAD_SAMPLE_MISSING_MESSAGE = """Data not present, please clone to your home directory e.g.
git clone https://github.com/mantidproject/mantidimaging-data.git ~/mantidimaging-data-master"""

SHOW_DELAY = 10  # Can be increased to watch tests
SHORT_DELAY = 100
LOAD_DELAY = 5000

uncaught_exception = None
current_excepthook = sys.excepthook


def handle_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    """
    Qt slots swallows exceptions. We need to catch them, but not exit.
    """
    global uncaught_exception
    # store first exception caught
    if uncaught_exception is None:
        uncaught_exception = f"{exc_type=}, {exc_value=}"

    current_excepthook(exc_type, exc_value, exc_traceback)


sys.excepthook = handle_uncaught_exceptions


@pytest.mark.system
@unittest.skipUnless(os.path.exists(LOAD_SAMPLE), LOAD_SAMPLE_MISSING_MESSAGE)
class GuiSystemBase(unittest.TestCase):
    app: QApplication

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def setUp(self) -> None:
        global uncaught_exception
        uncaught_exception = None
        self.main_window = MainWindowView()
        self.main_window.show()
        QTest.qWait(SHORT_DELAY)

    def tearDown(self) -> None:
        QTimer.singleShot(SHORT_DELAY, lambda: self._click_messageBox("Yes"))
        self.main_window.close()
        QTest.qWait(SHORT_DELAY)

        if uncaught_exception is not None:
            pytest.fail(f"Uncaught exception {uncaught_exception}")

    @classmethod
    def _click_messageBox(cls, button_text: str):
        """Needs to be queued with QTimer.singleShot before triggering the message box"""
        for widget in cls.app.topLevelWidgets():
            if isinstance(widget, QMessageBox):
                for button in widget.buttons():
                    if button.text().replace("&", "") == button_text:
                        QTest.mouseClick(button, Qt.LeftButton)
                        return
                button_texts = [button.text() for button in widget.buttons()]
                raise ValueError(f"Could not find button '{button_text}' in {button_texts}")

    def _close_welcome(self):
        self.main_window.welcome_window.view.close()

    @mock.patch("mantidimaging.gui.windows.load_dialog.view.MWLoadDialog.select_file")
    def _load_data_set(self, mocked_select_file):
        mocked_select_file.return_value = LOAD_SAMPLE
        self.main_window.actionLoadDataset.trigger()
        QTest.qWait(SHOW_DELAY)
        self.main_window.load_dialogue.presenter.notify(Notification.UPDATE_ALL_FIELDS)
        QTest.qWait(SHOW_DELAY)
        self.main_window.load_dialogue.accept()
        QTest.qWait(LOAD_DELAY)

    def _open_operations(self):
        self.main_window.actionFilters.trigger()

    def _open_reconstruction(self):
        self.main_window.actionRecon.trigger()

    def _close_stack_tabs(self):
        stack_tabs = self.main_window.presenter.model.get_all_stack_visualisers()
        while stack_tabs:
            last_stack_tab = stack_tabs.pop()
            QTimer.singleShot(SHORT_DELAY, lambda: self._click_messageBox("OK"))
            last_stack_tab.close()
            QTest.qWait(SHOW_DELAY // 10)
