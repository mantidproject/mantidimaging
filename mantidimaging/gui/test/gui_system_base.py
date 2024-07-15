# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
from pathlib import Path
import unittest
from unittest import mock

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog
import pytest

from mantidimaging.core.utility.leak_tracker import leak_tracker
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.test_helpers.qt_test_helpers import wait_until
from mantidimaging.test_helpers import start_qapplication, mock_versions

LOAD_SAMPLE = str(Path.home()) + "/mantidimaging-data/ISIS/IMAT/IMAT00010675/Tomo/IMAT_Flower_Tomo_000000.tif"
LOAD_SAMPLE_MISSING_MESSAGE = """Data not present, please clone to your home directory e.g.
git clone https://github.com/mantidproject/mantidimaging-data.git"""

SHOW_DELAY = 10  # Can be increased to watch tests
SHORT_DELAY = 100


@mock_versions
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
        """
        Closes the main window
        Will report any leaked images
        Expects all other windows to be closed, otherwise will raise a RuntimeError
        """
        QTimer.singleShot(SHORT_DELAY, lambda: self._click_messageBox("Yes"))
        self.main_window.close()
        QTest.qWait(SHORT_DELAY)
        self.assertDictEqual(self.main_window.presenter.model.datasets, {})

        if leak_count := leak_tracker.count():
            print("\nItems still alive:", leak_count)
            leak_tracker.pretty_print(debug_init=False, debug_owners=False, trace_depth=5)
            leak_tracker.clear()

        for widget in self.app.topLevelWidgets():
            if widget.isVisible():
                RuntimeError(f"\n\nWindow still open {widget=}")

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
    def _click_InputDialog(cls, set_int: int | None = None):
        """
        Needs to be queued with QTimer.singleShot before triggering the message box
        Will raise a RuntimeError if a QInputDialog is not found
        """
        for widget in cls.app.topLevelWidgets():
            if isinstance(widget, QInputDialog) and widget.isVisible():
                if set_int:
                    widget.setIntValue(set_int)
                QTest.qWait(SHORT_DELAY)
                widget.accept()
                return
        raise RuntimeError("_click_InputDialog did not find QInputDialog")

    def _close_welcome(self):
        self.main_window.welcome_window.view.close()

    @classmethod
    def _wait_for_widget_visible(cls, widget_type, delay=0.1, max_retry=100):
        for _ in range(max_retry):
            for widget in cls.app.topLevelWidgets():
                if isinstance(widget, widget_type) and widget.isVisible():
                    return True
        QTest.qWait(int(delay * 1000))
        raise RuntimeError("_wait_for_stack_selector reach max retries")

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.view.ImageLoadDialog.select_file")
    def _load_data_set(self, mocked_select_file):
        mocked_select_file.return_value = LOAD_SAMPLE
        initial_stacks = len(self.main_window.presenter.get_active_stack_visualisers())

        def test_func() -> bool:
            current_stacks = len(self.main_window.presenter.get_active_stack_visualisers())
            return (current_stacks - initial_stacks) >= 5

        self.main_window.actionLoadDataset.trigger()
        QTest.qWait(SHOW_DELAY)
        self.main_window.image_load_dialog.presenter.do_update_field(self.main_window.image_load_dialog.sample)
        QTest.qWait(SHOW_DELAY)
        self.main_window.image_load_dialog.accept()
        wait_until(test_func, max_retry=600)

    def _open_operations(self):
        self.main_window.actionFilters.trigger()

    def _open_reconstruction(self):
        self.main_window.actionRecon.trigger()

    def _open_spectrum_viewer(self):
        self.main_window.actionSpectrumViewer.trigger()

    def _close_image_stacks(self):
        while self.main_window.dataset_tree_widget.topLevelItemCount():
            self.main_window.dataset_tree_widget.topLevelItem(0).setSelected(True)
            self.main_window._delete_container()

    @classmethod
    def _close_window(cls, window_type):
        cls._wait_for_widget_visible(window_type)
        for widget in cls.app.topLevelWidgets():
            if isinstance(widget, window_type):
                QTest.qWait(SHORT_DELAY)
                widget.close()
