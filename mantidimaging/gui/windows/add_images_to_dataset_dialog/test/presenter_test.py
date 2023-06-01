# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from unittest import mock

from mantidimaging.gui.windows.add_images_to_dataset_dialog.presenter import AddImagesToDatasetPresenter, Notification


class AddImagesToDatasetPresenterTest(unittest.TestCase):

    def setUp(self):
        self.view = mock.MagicMock()
        self.presenter = AddImagesToDatasetPresenter(self.view)

    def test_load_images(self):

        self.view.path = test_path = "test/path"
        with mock.patch("mantidimaging.gui.windows.add_images_to_dataset_dialog.presenter.start_async_task_view"
                        ) as mock_start_async_task_view:
            self.presenter.load_images()

        mock_start_async_task_view.assert_called_once_with(self.view,
                                                           self.view.parent_view.presenter.model.load_image_stack,
                                                           self.presenter._on_images_load_done,
                                                           {'file_path': test_path})

    def test_load_images_successful(self):
        mock_task = mock.Mock()
        mock_task.was_successful.return_value = True

        self.presenter._on_images_load_done(mock_task)
        self.assertIs(self.presenter.images, mock_task.result)
        self.view.parent_view.execute_add_to_dataset.assert_called_once()

    def test_load_images_failure(self):
        mock_task = mock.Mock()
        mock_task.was_successful.return_value = False
        self.presenter.show_error = mock.Mock()

        self.presenter._on_images_load_done(mock_task)
        self.assertIsNone(self.presenter.images)
        self.view.parent_view.execute_add_to_dataset.assert_not_called()
        self.presenter.show_error.assert_called_once()

    def test_notify_runtime_error(self):
        self.presenter.load_images = mock.Mock(side_effect=RuntimeError)
        self.presenter.notify(Notification.IMAGE_FILE_SELECTED)
        self.view.show_exception.assert_called_once()
