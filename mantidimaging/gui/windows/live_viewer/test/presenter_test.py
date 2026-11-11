# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from parameterized import parameterized

from mantidimaging.gui.windows.live_viewer import LiveViewerWindowView, LiveViewerWindowModel, LiveViewerWindowPresenter
from mantidimaging.gui.windows.live_viewer.model import Image_Data, ImageCache
from mantidimaging.gui.windows.main import MainWindowView


class MainWindowPresenterTest(unittest.TestCase):

    def setUp(self):
        self.view = mock.create_autospec(LiveViewerWindowView, instance=True)
        self.main_window = mock.create_autospec(MainWindowView, instance=True)
        self.model = mock.create_autospec(LiveViewerWindowModel, instance=True)
        self.model.image_cache = mock.create_autospec(ImageCache, instance=True)
        self.model.mean_nan_mask = mock.create_autospec(np.ma.MaskedArray, instance=True)

        with mock.patch("mantidimaging.gui.windows.live_viewer.presenter.LiveViewerWindowModel") as mock_model:
            mock_model.return_value = self.model
            self.presenter = LiveViewerWindowPresenter(self.view, self.main_window)

    def test_load_as_dataset(self):
        image_dir = Path("/path/to/dir")
        image_paths = [image_dir / f"image_{i:03d}.tif" for i in range(5)]
        self.model.images = [mock.create_autospec(Image_Data, image_path=p, instance=True) for p in image_paths]
        self.presenter.load_as_dataset()
        self.main_window.show_image_load_dialog_with_path.assert_called_once_with(image_dir)

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
        self.model.images = image_list
        self.presenter.roi_moving = True
        self.view.live_viewer = mock.Mock()
        self.view.intensity_profile = mock.Mock()
        self.model.mean_readable = []
        self.view.intensity_action = mock.Mock()
        self.view.intensity_action.isChecked = mock.Mock()
        self.view.intensity_action.isChecked.return_value = False
        with mock.patch.object(self.presenter, "handle_deleted"):
            self.presenter.update_image_list()

        self.view.set_load_as_dataset_enabled.assert_called_once_with(action_enabled)

    def test_WHEN_initial_single_image_THEN_mean_is_added(self):
        image = mock.Mock(image_path=Path("/images/1.tif"))
        self.presenter.old_image_list_paths = []
        self.presenter.try_add_mean = mock.Mock()
        self.presenter.update_intensity = mock.Mock()
        self.presenter.handle_roi_moved = mock.Mock()

        self.presenter._update_intensity_for_images([image])

        self.presenter.try_add_mean.assert_called_once_with(image)
        self.presenter.handle_roi_moved.assert_not_called()

    def test_WHEN_images_are_appended_THEN_only_new_images_added(self):
        old_image = mock.Mock(image_path=Path("/images/1.tif"))
        new_image = mock.Mock(image_path=Path("/images/2.tif"))
        self.presenter.old_image_list_paths = [old_image.image_path]
        self.presenter.try_add_mean = mock.Mock()
        self.presenter.update_intensity = mock.Mock()
        self.presenter.handle_roi_moved = mock.Mock()

        self.presenter._update_intensity_for_images([old_image, new_image])

        self.presenter.try_add_mean.assert_called_once_with(new_image)
        self.presenter.update_intensity.assert_called_once_with(self.model.mean_nan_mask)
        self.presenter.handle_roi_moved.assert_not_called()
        self.assertEqual(
            self.presenter.old_image_list_paths,
            [old_image.image_path, new_image.image_path],
        )

    def test_WHEN_image_list_is_unchanged_THEN_chunk_count_resets_AND_roi_is_refreshed(self):
        old_paths = [Path("/images/1.tif"), Path("/images/2.tif")]
        new_images = [
            mock.Mock(image_path=Path("/images/new1.tif")),
            mock.Mock(image_path=Path("/images/new2.tif")),
        ]

        self.presenter.old_image_list_paths = old_paths.copy()
        self.presenter.try_next_mean_chunk_count = 5
        self.presenter.try_add_mean = mock.Mock()
        self.presenter.update_intensity = mock.Mock()
        self.presenter.handle_roi_moved = mock.Mock()

        self.presenter._update_intensity_for_images(new_images)

        self.assertEqual(self.presenter.try_next_mean_chunk_count, 0)
        self.presenter.handle_roi_moved.assert_called_once_with(force_clear=True)
        self.presenter.try_add_mean.assert_not_called()

    def test_WHEN_thread_is_running_THEN_recalculation_is_deferred(self):
        self.presenter.thread = mock.Mock()
        self.presenter.thread.isRunning.return_value = True
        self.presenter.recalc_pending = False

        with mock.patch("mantidimaging.gui.windows.live_viewer.presenter.TaskWorkerThread") as worker_class:
            self.presenter.handle_roi_moved()

        self.assertTrue(self.presenter.recalc_pending)
        worker_class.assert_not_called()
        self.model.clear_mean_partial.assert_not_called()

    @parameterized.expand([
        ("new_forced_request", False, True, True),
        ("preserve_forced_request", True, False, True),
        ("normal_request", False, False, False),
    ])
    def test_WHEN_thread_is_running_THEN_force_clear_requests_preserved_(self, _, pending_force_clear, force_clear,
                                                                         expected):
        self.presenter.thread = mock.Mock()
        self.presenter.thread.isRunning.return_value = True
        self.presenter.recalc_pending_force_clear = pending_force_clear

        self.presenter.handle_roi_moved(force_clear=force_clear)

        self.assertEqual(self.presenter.recalc_pending_force_clear, expected)

    @parameterized.expand([
        ("forced", True),
        ("not_forced", False),
    ])
    def test_WHEN_roi_is_unchanged_THEN_mean_is_cleared_only_if_forced(self, _, force_clear):
        roi = (0, 0, 10, 10)
        self.view.live_viewer = mock.Mock()
        self.view.live_viewer.get_roi.return_value = roi
        self.model.roi = roi
        self.presenter.thread = None
        self.presenter.set_roi_enabled = mock.Mock()

        with mock.patch("mantidimaging.gui.windows.live_viewer.presenter.TaskWorkerThread"):
            self.presenter.handle_roi_moved(force_clear=force_clear)

        if force_clear:
            self.model.clear_mean_partial.assert_called_once()
        else:
            self.model.clear_mean_partial.assert_not_called()

    def test_WHEN_worker_finihses_THEN_origional_worker_cleaned_up(self):
        self.view.live_viewer = mock.Mock()
        self.view.live_viewer.get_roi.return_value = None
        self.model.roi = None
        self.presenter.thread = None
        self.presenter.set_roi_enabled = mock.Mock()
        self.presenter.thread_cleanup = mock.Mock()

        with mock.patch("mantidimaging.gui.windows.live_viewer.presenter.TaskWorkerThread") as worker_class:
            worker = worker_class.return_value
            self.presenter.handle_roi_moved()

        callback = worker.finished.connect.call_args.args[0]
        self.presenter.thread = mock.Mock()

        callback()

        self.presenter.thread_cleanup.assert_called_once_with(worker)

    def test_WHEN_recalc_pending_THEN_request_started(self):
        self.presenter.recalc_pending = True
        self.presenter.recalc_pending_force_clear = True
        self.presenter.update_intensity_with_mean = mock.Mock()
        self.presenter.set_roi_enabled = mock.Mock()

        with mock.patch.object(self.presenter, "handle_roi_moved") as recalc:
            self.presenter.thread_cleanup(mock.Mock(error=None))

        recalc.assert_called_once_with(force_clear=True)
        self.assertFalse(self.presenter.recalc_pending)
        self.assertFalse(self.presenter.recalc_pending_force_clear)

    def test_WHEN_handle_notify_roi_moved_THEN_timer_started(self):
        self.presenter.handle_roi_change_timer = mock.Mock()
        self.presenter.handle_roi_change_timer.isActive.return_value = False
        self.presenter.handle_notify_roi_moved()
        self.presenter.handle_roi_change_timer.start.assert_called_once()

    def test_WHEN_nans_in_mean_THEN_handle_roi_change_timer_start(self):
        self.model.mean_nan_mask = np.ma.asarray([1, 2, 3, np.nan])
        self.presenter.handle_roi_change_timer = mock.Mock()
        self.presenter.handle_roi_change_timer.isActive.return_value = False
        self.model.images = np.empty(4)
        self.presenter.try_next_mean_chunk()
        self.presenter.handle_roi_change_timer.start.assert_called_once_with(10)

    def test_WHEN_no_nans_in_mean_THEN_handle_roi_change_timer_not_started(self):
        self.model.mean_nan_mask = np.ma.asarray([1, 2, 3, 4])
        self.presenter.handle_roi_change_timer = mock.Mock()
        self.presenter.handle_roi_change_timer.isActive.return_value = False
        self.model.images = np.empty(4)
        mock_thread = mock.Mock()
        mock_thread.error = None
        self.presenter.set_roi_enabled = mock.Mock()
        self.presenter.update_intensity_with_mean = mock.Mock()
        self.presenter.thread_cleanup(mock_thread)
        self.presenter.handle_roi_change_timer.start.assert_not_called()

    def test_WHEN_thread_error_raised_THEN_error_caught_and_logged(self):
        self.model.mean_nan_mask = np.ma.asarray([1, 2, 3, 4])
        self.presenter.handle_roi_change_timer = mock.Mock()
        self.presenter.handle_roi_change_timer.isActive.return_value = False
        self.model.images = np.empty(4)
        mock_thread = mock.Mock()
        mock_thread.error = ValueError()
        self.presenter.set_roi_enabled = mock.Mock()
        self.presenter.update_intensity_with_mean = mock.Mock()
        with self.assertRaises(ValueError):
            self.presenter.thread_cleanup(mock_thread)
        self.presenter.handle_roi_change_timer.start.assert_not_called()
