# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PyQt5.QtCore import QTimer, pyqtSignal
from parameterized import parameterized

from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.windows.live_viewer import LiveViewerWindowView, LiveViewerWindowModel, LiveViewerWindowPresenter
from mantidimaging.gui.windows.live_viewer.model import Image_Data
from mantidimaging.gui.windows.live_viewer.presenter import Worker
from mantidimaging.gui.windows.main import MainWindowView


class MainWindowPresenterTest(unittest.TestCase):

    def setUp(self):
        self.view = mock.create_autospec(LiveViewerWindowView, instance=True)
        self.main_window = mock.create_autospec(MainWindowView, instance=True)
        self.model = mock.create_autospec(LiveViewerWindowModel, instance=True)

        with mock.patch("mantidimaging.gui.windows.live_viewer.presenter.LiveViewerWindowModel") as mock_model:
            mock_model.return_value = self.model
            self.presenter = LiveViewerWindowPresenter(self.view, self.main_window)

    def test_load_as_dataset(self):
        image_dir = Path("/path/to/dir")
        image_paths = [image_dir / f"image_{i:03d}.tif" for i in range(5)]
        self.model.images = [mock.create_autospec(Image_Data, image_path=p, instance=True) for p in image_paths]

        self.presenter.load_as_dataset()

        self.main_window.show_image_load_dialog_with_path.assert_called_once_with(str(image_dir))

    def test_load_as_dataset_empty_dir(self):
        self.model.images = []

        self.presenter.load_as_dataset()

        self.main_window.show_image_load_dialog_with_path.assert_not_called()

    @parameterized.expand([
        ([], False),
        ([mock.Mock()], True),
    ])
    def test_load_as_dataset_enabled_when_images(self, image_list, action_enabled):
        self.model.set_roi = mock.Mock()
        self.model.mean_paths = set()
        self.model.mean = []
        self.model.image_cache = mock.Mock()
        self.model.add_mean = mock.Mock()
        self.presenter.roi_moving = True
        self.view.live_viewer = mock.Mock()
        self.view.intensity_profile = mock.Mock()
        with mock.patch.object(self.presenter, "handle_deleted"):
            self.presenter.update_image_list(image_list)

        self.view.set_load_as_dataset_enabled.assert_called_once_with(action_enabled)

    def test_WHEN_handle_notify_roi_moved_THEN_timer_started(self):
        self.presenter.handle_roi_change_timer = mock.Mock()
        self.presenter.handle_roi_change_timer.isActive.return_value = False
        self.presenter.handle_notify_roi_moved()
        self.presenter.handle_roi_change_timer.start.assert_called_once()

    def test_WHEN_nans_in_mean_THEN_handle_roi_change_timer_start(self):
        self.model.mean = np.array([1, 2, 3, np.nan])
        self.presenter.handle_roi_change_timer = mock.Mock()
        self.presenter.handle_roi_change_timer.isActive.return_value = False
        self.presenter.try_next_mean_chunk()
        self.presenter.handle_roi_change_timer.start.assert_called_once_with(100)

    def test_WHEN_no_nans_in_mean_THEN_handle_roi_change_timer_not_started(self):
        self.model.mean = np.array([1, 2, 3, 4])
        self.presenter.handle_roi_change_timer = mock.Mock()
        self.presenter.handle_roi_change_timer.isActive.return_value = False
        self.presenter.try_next_mean_chunk()
        self.presenter.handle_roi_change_timer.start.assert_not_called()




