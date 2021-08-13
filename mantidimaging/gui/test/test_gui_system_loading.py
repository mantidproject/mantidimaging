# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from pathlib import Path
from unittest import mock

from PyQt5.QtCore import QTimer, QEventLoop
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
import pytest

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHORT_DELAY, LOAD_SAMPLE, LOAD_DELAY
from mantidimaging.gui.widgets.stack_selector_dialog.stack_selector_dialog import StackSelectorDialog


class TestGuiSystemLoading(GuiSystemBase):
    def setUp(self) -> None:
        super().setUp()
        self._close_welcome()

    @mock.patch("mantidimaging.gui.windows.main.MainWindowView._get_file_name")
    def _load_images(self, mocked_select_file):
        mocked_select_file.return_value = LOAD_SAMPLE
        self.main_window.actionLoadImages.trigger()
        QTest.qWait(LOAD_DELAY)

    @classmethod
    def _click_stack_selector(cls):
        for widget in cls.app.topLevelWidgets():
            if isinstance(widget, StackSelectorDialog):
                for x in range(20):
                    QApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, SHORT_DELAY)
                    if widget.stack_selector_widget.currentText():
                        break
                else:
                    raise RuntimeError("Timed out waiting for StackSelectorDialog to populate")

                widget.ok_button.click()

    @pytest.mark.xfail(reason="Bug #1095")
    @mock.patch("mantidimaging.gui.windows.main.MainWindowView._get_file_name")
    def test_load_180(self, mocked_select_file):
        path_180 = Path(LOAD_SAMPLE).parents[1] / "180deg" / "IMAT_Flower_180deg_000000.tif"
        mocked_select_file.return_value = path_180
        self._load_images()
        stacks = self.main_window.presenter.get_all_stack_visualisers()

        self.assertEqual(len(stacks), 1)
        self.assertFalse(stacks[0].presenter.images.has_proj180deg())

        QTimer.singleShot(SHORT_DELAY * 10, lambda: self._click_stack_selector())
        self.main_window.actionLoad180deg.trigger()
        QTest.qWait(LOAD_DELAY)

        stacks_after = self.main_window.presenter.get_all_stack_visualisers()
        self.assertEqual(len(stacks_after), 2)
        self.assertIn(stacks[0], stacks_after)
        self.assertTrue(stacks[0].presenter.images.has_proj180deg())
