# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
from pathlib import Path
import unittest

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox
import pytest

from mantidimaging.core.utility.version_check import versions
from mantidimaging.gui.windows.main import MainWindowView

versions._use_test_values()

LOAD_SAMPLE = str(Path.home()) + "/mantidimaging-data-master/ISIS/IMAT/IMAT00010675/Tomo/IMAT_Flower_Tomo_000000.tif"
LOAD_SAMPLE_MISSING_MESSAGE = """Data not present, please clone to your home directory e.g.
git clone https://github.com/mantidproject/mantidimaging-data.git ~/mantidimaging-data-master"""

SHOW_DELAY = 10  # Can be increased to watch tests
SHORT_DELAY = 100
LOAD_DELAY = 5000


@pytest.mark.system
@unittest.skipUnless(os.path.exists(LOAD_SAMPLE), LOAD_SAMPLE_MISSING_MESSAGE)
class TestMainWindow(unittest.TestCase):
    app: QApplication

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def setUp(self) -> None:
        self.main_window = MainWindowView()
        self.main_window.show()
        QTest.qWait(SHORT_DELAY)

    def tearDown(self) -> None:
        QTimer.singleShot(SHORT_DELAY, lambda: self._click_messageBox("Yes"))
        self.main_window.close()
        QTest.qWait(SHORT_DELAY)

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

    def test_main_window_shows(self):
        self.assertTrue(self.main_window.isVisible())
        self.assertTrue(self.main_window.welcome_window.view.isVisible())
        QTest.qWait(SHOW_DELAY)
        self._close_welcome()
        self.assertFalse(self.main_window.welcome_window.view.isVisible())
        QTest.qWait(SHOW_DELAY)
