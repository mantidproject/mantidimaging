# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from unittest import mock

import numpy as np

from mantidimaging.core.operations.loader import load_filter_packages
from mantidimaging.gui.windows.live_viewer.model import Image_Data
from mantidimaging.test_helpers.unit_test_helper import FakeFSTestCase
from pathlib import Path

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


class LiveViewerWindowTest(FakeFSTestCase, BaseEyesTest):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_filter_packages()  # Needs to be called before pyfakefs hides the filesystem

    def setUp(self) -> None:
        super().setUp()
        self.fs.add_real_directory(Path(__file__).parent.parent)  # Allow ui file to be found
        self.live_directory = Path("/live_dir")
        self.fs.create_dir(self.live_directory)

    def _generate_image(self):
        image = np.zeros((10, 10))
        image[5, :] = np.arange(10)
        return image

    def _make_simple_dir(self, directory: Path):
        file_list = [directory / f"abc_{i:06d}.tif" for i in range(5)]
        if not directory.exists():
            self.fs.create_dir(directory)

        for file in file_list:
            self.fs.create_file(file)

        return file_list

    @mock.patch('mantidimaging.gui.windows.live_viewer.model.ImageWatcher')
    def test_live_view_opens_without_data(self, _mock_image_watcher):
        self.imaging.show_live_viewer(self.live_directory)
        self.check_target(widget=self.imaging.live_viewer)

    @mock.patch('mantidimaging.gui.windows.live_viewer.presenter.LiveViewerWindowPresenter.load_image')
    @mock.patch('mantidimaging.gui.windows.live_viewer.model.ImageWatcher')
    def test_live_view_opens_with_data(self, _mock_image_watcher, mock_load_image):
        file_list = self._make_simple_dir(self.live_directory)
        image_list = [Image_Data(path) for path in file_list]
        mock_load_image.return_value = self._generate_image()
        self.imaging.show_live_viewer(self.live_directory)
        self.imaging.live_viewer.presenter.model._handle_image_changed_in_list(image_list)
        self.check_target(widget=self.imaging.live_viewer)

    @mock.patch('mantidimaging.gui.windows.live_viewer.presenter.LiveViewerWindowPresenter.load_image')
    @mock.patch('mantidimaging.gui.windows.live_viewer.model.ImageWatcher')
    def test_live_view_opens_with_bad_data(self, _mock_image_watcher, mock_load_image):
        file_list = self._make_simple_dir(self.live_directory)
        image_list = [Image_Data(path) for path in file_list]
        mock_load_image.side_effect = ValueError
        self.imaging.show_live_viewer(self.live_directory)
        self.imaging.live_viewer.presenter.model._handle_image_changed_in_list(image_list)
        self.check_target(widget=self.imaging.live_viewer)
