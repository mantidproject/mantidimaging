# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from parameterized import parameterized

from mantidimaging.gui.windows.live_viewer import LiveViewerWindowView, LiveViewerWindowModel, LiveViewerWindowPresenter
from mantidimaging.gui.windows.live_viewer.model import Image_Data
from mantidimaging.gui.windows.main import MainWindowView


class MainWindowPresenterTest(unittest.TestCase):

    def setUp(self):
        self.view = mock.create_autospec(LiveViewerWindowView)
        self.main_window = mock.create_autospec(MainWindowView)
        self.model = mock.create_autospec(LiveViewerWindowModel)

        with mock.patch("mantidimaging.gui.windows.live_viewer.presenter.LiveViewerWindowModel") as mock_model:
            mock_model.return_value = self.model
            self.presenter = LiveViewerWindowPresenter(self.view, self.main_window)

    def test_load_as_dataset(self):
        image_dir = Path("/path/to/dir")
        image_paths = [image_dir / f"image_{i:03d}.tif" for i in range(5)]
        self.model.images = [mock.create_autospec(Image_Data, image_path=p) for p in image_paths]

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
        with mock.patch.object(self.presenter, "handle_deleted"):
            self.presenter.update_image_list(image_list)

        self.view.set_load_as_dataset_enabled.assert_called_once_with(action_enabled)
