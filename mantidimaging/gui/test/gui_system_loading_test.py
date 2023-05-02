# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import math
import os
import tempfile
from pathlib import Path
from unittest import mock

import numpy
from PyQt5.QtCore import Qt, QTimer, QEventLoop
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QDialogButtonBox

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHORT_DELAY, LOAD_SAMPLE
from mantidimaging.gui.widgets.dataset_selector_dialog.dataset_selector_dialog import DatasetSelectorDialog
from mantidimaging.gui.windows.main.image_save_dialog import ImageSaveDialog
from mantidimaging.test_helpers.qt_test_helpers import wait_until


class TestGuiSystemLoading(GuiSystemBase):
    def setUp(self) -> None:
        super().setUp()
        self._close_welcome()

    def tearDown(self) -> None:
        self._close_image_stacks()
        super().tearDown()
        self.assertFalse(self.main_window.isVisible())

    @mock.patch("mantidimaging.gui.windows.main.MainWindowView._get_file_name")
    def _load_images(self, mocked_select_file):
        mocked_select_file.return_value = LOAD_SAMPLE
        initial_stacks = len(self.main_window.presenter.get_active_stack_visualisers())

        self.main_window.actionLoadImages.trigger()

        def test_func() -> bool:
            current_stacks = len(self.main_window.presenter.get_active_stack_visualisers())
            return (current_stacks - initial_stacks) >= 1

        wait_until(test_func, max_retry=600)

    @classmethod
    def _click_stack_selector(cls):
        cls._wait_for_widget_visible(DatasetSelectorDialog)
        for widget in cls.app.topLevelWidgets():
            if isinstance(widget, DatasetSelectorDialog):
                for _ in range(20):
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

        wait_until(lambda: len(self.main_window.presenter.get_active_stack_visualisers()) == 5)

        stacks_after = self.main_window.presenter.get_active_stack_visualisers()
        self.assertEqual(len(stacks_after), 5)
        self.assertIn(stacks[0], stacks_after)
        self.assertTrue(stacks[0].presenter.images.has_proj180deg())

    def _get_log_angle(self, log_path):
        with open(log_path) as log_file:
            for line in log_file:
                if "Projection:  1" in line:
                    words = line.split()
                    angle = float(words[words.index("angle:") + 1])
                    return angle
        raise ValueError(f"Could not extract angle from: {log_path}")

    @mock.patch("mantidimaging.gui.windows.main.MainWindowView._get_file_name")
    def test_load_log(self, mocked_select_file):
        log_path = Path(LOAD_SAMPLE).parents[1] / "TomoIMAT00010675_FlowerFine_log.txt"
        mocked_select_file.return_value = log_path
        self.assertEqual(len(self.main_window.presenter.get_active_stack_visualisers()), 0)
        self._load_data_set()
        self.assertEqual(len(self.main_window.presenter.get_active_stack_visualisers()), 5)

        self.assertEqual(len(self.main_window.presenter.datasets), 1)
        sample = list(self.main_window.presenter.datasets)[0].sample
        self.assertNotIn("log_file", sample.metadata)

        # Initial angles are just evenly spaced from 0 to 2*pi
        stack_len = sample.num_images
        self.assertAlmostEqual(sample.projection_angles().value[1], 2 * math.pi / (stack_len - 1), 12)

        # Load sample log
        QTimer.singleShot(SHORT_DELAY, lambda: self._click_stack_selector())
        QTimer.singleShot(SHORT_DELAY * 2, lambda: self._click_messageBox("OK"))
        self.main_window.actionSampleLoadLog.trigger()

        self.assertIn("log_file", sample.metadata)
        self.assertEqual(sample.metadata['log_file'], str(log_path))

        # After loading angles should match file
        log_angle = math.radians(self._get_log_angle(log_path))
        self.assertAlmostEqual(sample.projection_angles().value[1], log_angle, 12)

    def _make_angles_file(self, angles):
        angles_file = tempfile.NamedTemporaryFile("w", delete=False)
        angles_file.write(",".join(map(str, angles)))
        angles_file.close()
        return angles_file

    @mock.patch("mantidimaging.gui.windows.main.MainWindowView._get_file_name")
    def test_load_angles(self, mocked_select_file):
        self.assertEqual(len(self.main_window.presenter.get_active_stack_visualisers()), 0)
        self._load_data_set()
        self.assertEqual(len(self.main_window.presenter.get_active_stack_visualisers()), 5)

        self.assertEqual(len(self.main_window.presenter.datasets), 1)
        sample = list(self.main_window.presenter.datasets)[0].sample
        self.assertNotIn("log_file", sample.metadata)

        # Initial angles are just evenly spaced from 0 to 2*pi
        stack_len = sample.num_images
        self.assertAlmostEqual(sample.projection_angles().value[1], 2 * math.pi / (stack_len - 1), 12)

        test_angles = numpy.linspace(0, 100, stack_len)
        angle_file = self._make_angles_file(test_angles)

        mocked_select_file.return_value = angle_file.name

        # Load angles
        QTimer.singleShot(SHORT_DELAY, lambda: self._click_stack_selector())
        QTimer.singleShot(SHORT_DELAY * 2, lambda: self._click_messageBox("OK"))
        self.main_window.actionLoadProjectionAngles.trigger()

        # After loading angles should match file
        self.assertAlmostEqual(sample.projection_angles().value[1], math.radians(test_angles[1]), 12)
        os.remove(angle_file.name)

    def test_save_images(self):
        self._load_images()

        self.main_window.show_image_save_dialog()

        with mock.patch("mantidimaging.gui.windows.main.MainWindowModel.do_images_saving") as mock_save:
            self._wait_for_widget_visible(ImageSaveDialog)
            QApplication.processEvents()

            ok_button = self.main_window.image_save_dialog.buttonBox.button(QDialogButtonBox.StandardButton.SaveAll)
            QTest.mouseClick(ok_button, Qt.LeftButton)

            QApplication.processEvents()
            wait_until(lambda: mock_save.call_count == 1)
            # Confirm that save has been called only once
            mock_save.assert_called_once()
