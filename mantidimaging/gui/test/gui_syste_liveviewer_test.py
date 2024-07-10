# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path
from unittest import mock

from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHORT_DELAY, SHOW_DELAY, LOAD_SAMPLE
from mantidimaging.gui.windows.live_viewer.view import LiveViewerWindowView
from mantidimaging.test_helpers.qt_test_helpers import wait_until

LIVE_DIR_PATH = Path(LOAD_SAMPLE).parent


class TestLiveViewerLoading(GuiSystemBase):
    app: QApplication

    def setUp(self) -> None:
        super().setUp()
        self.live_viewer = LiveViewerWindowView(self.main_window, LIVE_DIR_PATH)
        self.live_viewer.show()
        QTest.qWait(SHORT_DELAY)

    def tearDown(self) -> None:
        self.live_viewer.close()
        super().tearDown()

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.view.ImageLoadDialog.select_file")
    def _load_data_set_and_wait(self, mocked_select_file) -> None:
        """Load the dataset and wait until it is fully loaded."""
        mocked_select_file.return_value = str(LOAD_SAMPLE)
        initial_images = len(self.live_viewer.presenter.model.images)

        self.live_viewer.presenter.set_dataset_path(LIVE_DIR_PATH)

        def test_func() -> bool:
            current_images = len(self.live_viewer.presenter.model.images)
            return (current_images - initial_images) >= 1

        wait_until(test_func, max_retry=600)

    def test_live_viewer_window_shows(self):
        """Test that the Live Viewer window is visible after creation."""
        self.assertTrue(self.live_viewer.isVisible())
        QTest.qWait(SHOW_DELAY)

    def test_load_images(self):
        self._load_data_set_and_wait()
        self.assertTrue(len(self.live_viewer.presenter.model.images) > 0)

    def test_image_rotation(self):
        """Test applying a rotation operation to an image and ensuring the filter_params are updated."""
        self._load_data_set_and_wait()
        self.live_viewer.presenter.select_image(0)
        self.live_viewer.rotate_angles_group.actions()[1].trigger()  # Rotate 90°
        self.assertIn("Rotate Stack", self.live_viewer.filter_params)
        self.assertEqual(self.live_viewer.filter_params["Rotate Stack"]["params"]["angle"], 90)
        QTest.qWait(SHOW_DELAY)

    def test_remove_image(self):
        """Test removing an image from the Live Viewer."""
        self._load_data_set_and_wait()
        self.live_viewer.presenter.select_image(0)
        self.live_viewer.remove_image()
        self.assertIsNone(self.live_viewer.live_viewer.image)
        QTest.qWait(SHOW_DELAY)

    def test_image_modified(self):
        """Test that the Live Viewer updates the image when it is modified."""
        self._load_data_set_and_wait()
        self.live_viewer.presenter.select_image(0)
        # Simulate an image modification
        QTimer.singleShot(SHORT_DELAY, lambda: self.live_viewer.presenter.update_image_modified(Path(LOAD_SAMPLE)))
        wait_until(lambda: self.live_viewer.live_viewer.image is not None, max_retry=100)
        self.assertIsNotNone(self.live_viewer.live_viewer.image)
        QTest.qWait(SHOW_DELAY)

    def test_image_range_slider(self):
        """Test setting the range of the z-slider and verifying the image index updates correctly."""
        self._load_data_set_and_wait()
        self.live_viewer.presenter.select_image(0)
        self.assertEqual(self.live_viewer.live_viewer.z_slider.value(), 0)
        self.live_viewer.set_image_range((0, 1))
        self.assertEqual(self.live_viewer.live_viewer.z_slider.maximum(), 1)
        self.live_viewer.set_image_index(1)
        self.assertEqual(self.live_viewer.live_viewer.z_slider.value(), 1)
        QTest.qWait(SHOW_DELAY)

    def test_open_operations_dialog(self):
        """Test that the Operations dialog opens correctly from the Live Viewer."""
        self._load_data_set_and_wait()
        self.live_viewer.presenter.select_image(0)
        self.live_viewer.right_click_menu.actions()[0].trigger()  # Open Operations menu
        self.assertIsNotNone(self.live_viewer.filters)
        self.assertTrue(self.live_viewer.filters.isVisible())
        QTest.qWait(SHOW_DELAY)
        self.live_viewer.filters.close()
        QTest.qWait(SHOW_DELAY)

    def test_set_image_rotation_angle(self):
        """Test setting the image rotation angle from the right-click menu."""
        self._load_data_set_and_wait()
        self.live_viewer.presenter.select_image(0)
        self.live_viewer.rotate_angles_group.actions()[2].trigger()  # Rotate 180°
        self.assertIn("Rotate Stack", self.live_viewer.filter_params)
        self.assertEqual(self.live_viewer.filter_params["Rotate Stack"]["params"]["angle"], 180)
        QTest.qWait(SHOW_DELAY)

    def test_image_display_after_operation(self):
        """Test that performing an operation on the image updates the display."""
        self._load_data_set_and_wait()
        self.live_viewer.presenter.select_image(0)
        self.assertIsNotNone(self.live_viewer.live_viewer.image)
        self.live_viewer.rotate_angles_group.actions()[1].trigger()  # Rotate 90°
        self.live_viewer.presenter.update_image_operation()
        self.assertIsNotNone(self.live_viewer.live_viewer.image)
        QTest.qWait(SHOW_DELAY)

    def test_handle_deleted(self):
        """Test that the image is removed and the label is cleared when an image is deleted."""
        self._load_data_set_and_wait()
        self.live_viewer.presenter.select_image(0)
        self.assertIsNotNone(self.live_viewer.live_viewer.image)
        self.live_viewer.presenter.model._handle_image_changed_in_list([])
        self.assertIsNone(self.live_viewer.live_viewer.image)
        self.assertEqual(self.live_viewer.label_active_filename.text(), "")
        self.assertEqual(self.live_viewer.live_viewer.z_slider.maximum(), 1)
        QTest.qWait(SHOW_DELAY)
