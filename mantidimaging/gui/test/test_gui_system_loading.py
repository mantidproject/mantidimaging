# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from pathlib import Path
from unittest import mock

from PyQt5.QtCore import Qt, QTimer, QEventLoop
from PyQt5.QtWidgets import QApplication

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHORT_DELAY, LOAD_SAMPLE
from mantidimaging.gui.widgets.dataset_selector_dialog.dataset_selector_dialog import DatasetSelectorDialog


class TestGuiSystemLoading(GuiSystemBase):
    def setUp(self) -> None:
        super().setUp()
        self._close_welcome()

    @mock.patch("mantidimaging.gui.windows.main.MainWindowView._get_file_name")
    def _load_images(self, mocked_select_file):
        mocked_select_file.return_value = LOAD_SAMPLE
        initial_stacks = len(self.main_window.presenter.get_active_stack_visualisers())

        self.main_window.actionLoadImages.trigger()

        def test_func() -> bool:
            current_stacks = len(self.main_window.presenter.get_active_stack_visualisers())
            return (current_stacks - initial_stacks) >= 1

        self._wait_until(test_func, max_retry=600)

    @classmethod
    def _click_stack_selector(cls):
        cls._wait_for_widget_visible(DatasetSelectorDialog)
        for widget in cls.app.topLevelWidgets():
            if isinstance(widget, DatasetSelectorDialog):
                for x in range(20):
                    QApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, SHORT_DELAY)
                    if widget.dataset_selector_widget.currentText():
                        break
                else:
                    raise RuntimeError("Timed out waiting for DatasetSelectorDialog to populate")

                widget.ok_button.click()

    def test_load_images(self):
        self._load_images()

    @mock.patch("mantidimaging.gui.windows.main.MainWindowView._get_file_name")
    def test_load_180(self, mocked_select_file):
        path_180 = Path(LOAD_SAMPLE).parents[1] / "180deg" / "IMAT_Flower_180deg_000000.tif"
        mocked_select_file.return_value = path_180
        self.assertEqual(len(self.main_window.presenter.get_active_stack_visualisers()), 0)
        self._load_data_set()
        stacks = self.main_window.presenter.get_active_stack_visualisers()
        self.assertEqual(len(self.main_window.presenter.get_active_stack_visualisers()), 5)

        # Remove existing 180
        proj180deg_entry = self.main_window.dataset_tree_widget.findItems("180", Qt.MatchFlag.MatchRecursive)
        self.assertEqual(len(proj180deg_entry), 1)
        self.main_window.dataset_tree_widget.setCurrentItem(proj180deg_entry[0])
        self.main_window._delete_container()

        self.assertFalse(stacks[0].presenter.images.has_proj180deg())
        self.assertEqual(len(self.main_window.presenter.get_active_stack_visualisers()), 4)

        # load new 180
        QTimer.singleShot(SHORT_DELAY, lambda: self._click_stack_selector())
        self.main_window.actionLoad180deg.trigger()

        self._wait_until(lambda: len(self.main_window.presenter.get_active_stack_visualisers()) == 5)

        stacks_after = self.main_window.presenter.get_active_stack_visualisers()
        self.assertEqual(len(stacks_after), 5)
        self.assertIn(stacks[0], stacks_after)
        self.assertTrue(stacks[0].presenter.images.has_proj180deg())
