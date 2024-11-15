# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
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
from parameterized import parameterized

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHORT_DELAY, LOAD_SAMPLE, SHOW_DELAY
from mantidimaging.gui.widgets.dataset_selector_dialog.dataset_selector_dialog import DatasetSelectorDialog
from mantidimaging.gui.windows.main.image_save_dialog import ImageSaveDialog
from mantidimaging.gui.windows.main.nexus_save_dialog import NexusSaveDialog
from mantidimaging.test_helpers.qt_test_helpers import wait_until


class TestGuiSystemLoading(GuiSystemBase):

    def setUp(self) -> None:
        super().setUp()
        self._close_welcome()

    def tearDown(self) -> None:
        self._close_image_stacks()
        self._check_datasets_consistent()
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
        self._check_datasets_consistent()

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
        self._check_datasets_consistent()

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
        self.assertIn("log_file", sample.metadata)

        sample.log_file = None
        sample._projection_angles = None
        self.assertNotIn("log_file", sample.metadata)

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
        self.assertIn("log_file", sample.metadata)

        sample.log_file = None
        sample._projection_angles = None
        self.assertNotIn("log_file", sample.metadata)

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

    def test_save_nexus(self):
        self._load_data_set()

        self.main_window.show_nexus_save_dialog()

        with mock.patch("mantidimaging.core.io.saver.nexus_save") as mock_save:
            self._wait_for_widget_visible(NexusSaveDialog)
            self.main_window.nexus_save_dialog.savePath.setText("/path/aaa.nxs")
            self.main_window.nexus_save_dialog.sampleNameLineEdit.setText("aaa")
            QApplication.processEvents()
            ok_button = self.main_window.nexus_save_dialog.buttonBox.button(QDialogButtonBox.StandardButton.Save)
            QTest.mouseClick(ok_button, Qt.LeftButton)

            QApplication.processEvents()
            wait_until(lambda: mock_save.call_count == 1)
            # Confirm that save has been called only once
            mock_save.assert_called_once()

    @parameterized.expand([
        (None, 100),
        ((0, 10, 1), 10),
        ((0, 100, 4), 25),
        ((20, 30, 1), 10),
    ])
    @mock.patch("mantidimaging.gui.windows.image_load_dialog.view.ImageLoadDialog.select_file")
    @mock.patch("mantidimaging.core.io.loader.loader._imread")
    def test_load_with_start_stop_inc(self, start_stop_inc, expected_count, mocked_imread, mocked_select_file):
        mocked_imread.return_value = numpy.zeros([128, 128])  # Don't need to actually load the files
        mocked_select_file.return_value = LOAD_SAMPLE
        self.assertEqual(len(self.main_window.presenter.get_active_stack_visualisers()), 0)

        self.main_window.actionLoadDataset.trigger()
        QTest.qWait(SHOW_DELAY)
        self.main_window.image_load_dialog.presenter.do_update_field(self.main_window.image_load_dialog.sample)
        QTest.qWait(SHOW_DELAY)

        if start_stop_inc is not None:
            start, stop, inc = start_stop_inc
            self.main_window.image_load_dialog.sample._start_spinbox.setValue(start)
            self.main_window.image_load_dialog.sample._stop_spinbox.setValue(stop)
            self.main_window.image_load_dialog.sample._increment_spinbox.setValue(inc)
            QTest.qWait(SHOW_DELAY)

        self.main_window.image_load_dialog.accept()

        def test_func() -> bool:
            current_stacks = len(self.main_window.presenter.get_active_stack_visualisers())
            return current_stacks >= 5

        wait_until(test_func, max_retry=600)

        self.assertEqual(len(self.main_window.presenter.get_active_stack_visualisers()), 5)

        sample = list(self.main_window.presenter.datasets)[0].sample
        image_count, *image_shape = sample.data.shape
        self.assertEqual(image_shape, [128, 128])
        self.assertEqual(image_count, expected_count)
        self.assertEqual(len(sample.real_projection_angles().value), expected_count)

    @mock.patch("mantidimaging.gui.windows.main.MainWindowView._get_file_name")
    def test_replace_image_stack(self, mocked_select_file):
        new_stack = Path(LOAD_SAMPLE).parents[1] / "Flat_Before/" / "IMAT_Flower_Flat_Before_000000.tif"
        mocked_select_file.return_value = new_stack
        self.assertEqual(len(self.main_window.presenter.get_active_stack_visualisers()), 0)
        self._load_data_set()
        self.assertEqual(len(self.main_window.presenter.get_active_stack_visualisers()), 5)
        self.assertEqual(100, list(self.main_window.presenter.datasets)[0].sample.data.shape[0])
        initial_sample_id = list(self.main_window.presenter.datasets)[0].sample.id

        self.main_window.dataset_tree_widget.topLevelItem(0).setSelected(True)
        self._check_datasets_consistent()

        self.main_window._add_images_to_existing_dataset()
        QTest.qWait(SHORT_DELAY)

        with mock.patch(
                "mantidimaging.gui.windows.add_images_to_dataset_dialog.view.QFileDialog.getOpenFileName") as gofn:
            gofn.return_value = (str(new_stack), None)
            self.main_window.add_to_dataset_dialog.chooseFileButton.click()

        self.main_window.add_to_dataset_dialog.accept()
        wait_until(lambda: initial_sample_id not in self.main_window.presenter.all_stack_ids)

        self._check_datasets_consistent()
        self.assertEqual(20, list(self.main_window.presenter.datasets)[0].sample.data.shape[0])

    def _check_datasets_consistent(self, show_datasets=False) -> None:
        if show_datasets:
            print("Main window datasets")
            for k, v in self.main_window.presenter.model.datasets.items():
                print("  dataset:", k)
                for image_stack in v.all:
                    print("    ", image_stack.id, image_stack.name)
            print("Main window visualisers/tabs")
            for vis in self.main_window.presenter.get_active_stack_visualisers():
                print("  ", vis.id, vis.name)
            print("Main window treeview")
            for i in range(self.main_window.dataset_tree_widget.topLevelItemCount()):
                tree_ds = self.main_window.dataset_tree_widget.topLevelItem(i)
                print(f"  dataset: {tree_ds.id} {tree_ds.text(0)}")
                for j in range(tree_ds.childCount()):
                    tree_is = tree_ds.child(j)
                    print(f"    {tree_is.id} {tree_is.text(0)}")

        # Datasets
        open_dataset_ids = list(self.main_window.presenter.model.datasets.keys())
        self.assertEqual(len(open_dataset_ids), len(set(open_dataset_ids)))
        image_stack_ids = self.main_window.presenter.model.image_ids
        self.assertEqual(len(image_stack_ids), len(set(image_stack_ids)))

        # Visualisers/Tabs
        visualiser_ids = [vis.id for vis in self.main_window.presenter.get_active_stack_visualisers()]
        self.assertEqual(len(visualiser_ids), len(set(visualiser_ids)))
        self.assertEqual(len(visualiser_ids), len(image_stack_ids))
        for visualiser_id in visualiser_ids:
            self.assertIn(visualiser_id, image_stack_ids)

        #Tree view
        tree_datasets = [
            self.main_window.dataset_tree_widget.topLevelItem(i)
            for i in range(self.main_window.dataset_tree_widget.topLevelItemCount())
        ]
        tree_image_stack_ids = []
        self.assertEqual(len(open_dataset_ids), len(tree_datasets))
        for tree_dataset in tree_datasets:
            self.assertIn(tree_dataset.id, open_dataset_ids)
            for i in range(tree_dataset.childCount()):
                tree_image_stack_ids.append(tree_dataset.child(i).id)
        self.assertEqual(len(tree_image_stack_ids), len(set(tree_image_stack_ids)))
        self.assertEqual(len(tree_image_stack_ids), len(image_stack_ids))
