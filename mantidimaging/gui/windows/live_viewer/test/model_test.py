# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import random
import time
import unittest

from pathlib import Path
from unittest import mock

import numpy as np
from PyQt5.QtCore import QFileSystemWatcher, pyqtSignal

from mantidimaging.gui.windows.live_viewer.model import ImageWatcher, ImageCache, Image_Data
from mantidimaging.test_helpers.unit_test_helper import FakeFSTestCase


class ImageWatcherTest(FakeFSTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.top_path = Path("/live")
        self.fs.create_dir(self.top_path)
        os.utime(self.top_path, (10, 10))
        with mock.patch("mantidimaging.gui.windows.live_viewer.model.QFileSystemWatcher") as mocker:
            mock_dir_watcher = mock.create_autospec(QFileSystemWatcher, directoryChanged=mock.Mock(), instance=True)
            mock_file_watcher = mock.create_autospec(QFileSystemWatcher, fileChanged=mock.Mock(), instance=True)

            mocker.side_effect = [mock_dir_watcher, mock_file_watcher]
            self.watcher = ImageWatcher(self.top_path)
            self.mock_signal_image = mock.create_autospec(pyqtSignal, emit=mock.Mock(), instance=True)
            self.watcher.image_changed = self.mock_signal_image

    def _make_simple_dir(self, directory: Path, t0: float = 1000):
        file_list = [directory / f"abc_{i:06d}.tif" for i in range(5)]
        if not directory.exists():
            self.fs.create_dir(directory)
        os.utime(directory, (10, t0))
        n = 1
        for file in file_list:
            self.fs.create_file(file)
            os.utime(file, (10, t0 + n))
            n += 1

        return file_list

    def _make_sub_directories(self, directory: Path, sub_dirs: list[str], t0: float = 1000):
        n = 0
        for sub_dir in sub_dirs:
            self.fs.create_dir(directory / sub_dir)
            os.utime(directory / sub_dir, (10, t0 + n))
            n += 1
            file_list = [directory / sub_dir / f"abc_{i:06d}.tiff" for i in range(5)]
            for file in file_list:
                self.fs.create_file(file)
                os.utime(file, (10, t0 + n))
                n += 1

        return file_list

    def _get_recent_emitted_files(self):
        self.mock_signal_image.emit.assert_called()
        last_call_args = self.mock_signal_image.emit.call_args_list[-1]
        emitted_images = [image_data.image_path for image_data in last_call_args[0][0]]
        return emitted_images

    def test_WHEN_find_images_called_THEN_returns_images(self):
        file_list = self._make_simple_dir(self.top_path)

        images_datas = self.watcher.find_images(self.top_path)

        images = [image.image_path for image in images_datas]
        self._file_list_count_equal(images, file_list)

    def test_WHEN_find_images_deleted_file_THEN_handles_error(self):
        # Simulate the case where a file returned by iterdir has been deleted when we come to read it
        file_list = self._make_simple_dir(self.top_path)
        self.fs.remove(file_list[0])

        # mocked iterdir() gives full list, but first file as been deleted
        mock_directory = mock.create_autospec(Path, iterdir=lambda: file_list, instance=True)

        images_datas = self.watcher.find_images(mock_directory)

        images = [image.image_path for image in images_datas]
        self._file_list_count_equal(images, file_list[1:])

    def test_WHEN_empty_dir_THEN_no_files(self):
        self.watcher.changed_directory = self.top_path
        self.watcher._handle_directory_change()

        emitted_images = self._get_recent_emitted_files()
        self._file_list_count_equal(emitted_images, [])

    def test_WHEN_missing_dir_THEN_useful_error(self):
        self.fs.rmdir(self.top_path)
        self.watcher.changed_directory = self.top_path

        with self.assertRaises(FileNotFoundError) as context_manager:
            self.watcher._handle_directory_change()
        self.assertIn("Live directory not found", str(context_manager.exception))
        self.assertIn(str(self.top_path), str(context_manager.exception))

    def test_WHEN_find_sub_directories_called_THEN_finds_subdirs(self):
        self._file_in_sequence(self.top_path, self.watcher.sub_directories.keys())
        self.assertEqual(len(self.watcher.sub_directories), 1)
        subdir_names = ["tomo", "flat_before", "flat_after"]
        self._make_sub_directories(self.top_path, subdir_names)

        self.watcher.find_sub_directories(self.top_path)
        for sub_dir in subdir_names:
            self._file_in_sequence(self.top_path / sub_dir, self.watcher.sub_directories.keys())

    def test_WHEN_directory_change_simple_THEN_images_emitted(self):
        file_list = self._make_simple_dir(self.top_path)
        self.mock_signal_image.emit.assert_not_called()

        self.watcher.changed_directory = self.top_path
        self.watcher._handle_directory_change()

        emitted_images = self._get_recent_emitted_files()
        self._file_list_count_equal(emitted_images, file_list)

    @mock.patch("time.time", return_value=4000.0)
    def test_WHEN_directory_change_empty_subdir_THEN_images_emitted(self, _mock_time):
        # empty sub dir created, but contains no images so should emit images from top dir
        file_list = self._make_simple_dir(self.top_path)
        self.fs.create_dir(self.top_path / "empty")
        os.utime(self.top_path / "empty", [10, 2000])
        self.assertLess(self.top_path.stat().st_mtime, (self.top_path / 'empty').stat().st_mtime)

        self.watcher.changed_directory = self.top_path / "empty"
        self.watcher._handle_directory_change()

        emitted_images = self._get_recent_emitted_files()
        self._file_list_count_equal(emitted_images, file_list)

    @mock.patch("time.time", return_value=4000.0)
    def test_WHEN_directory_change_with_subdir_THEN_images_emitted(self, _mock_time):
        # If change notification is on top dir, then emit top files even if subdir newer
        file_list = self._make_simple_dir(self.top_path)
        _ = self._make_simple_dir(self.top_path / "more", t0=2000)
        self.assertLess(self.top_path.stat().st_mtime, (self.top_path / 'more').stat().st_mtime)
        self.assertLess((self.top_path / 'more').stat().st_mtime, time.time())

        self.watcher.changed_directory = self.top_path
        self.watcher._handle_directory_change()

        emitted_images = self._get_recent_emitted_files()
        self._file_list_count_equal(emitted_images, file_list)

    @mock.patch("time.time", return_value=4000.0)
    def test_WHEN_sub_directory_change_THEN_images_emitted(self, _mock_time):
        # If change notification is on sub dir, then emit sub dir files
        _ = self._make_simple_dir(self.top_path)
        file_list2 = self._make_simple_dir(self.top_path / "more", t0=2000)
        self.assertLess(self.top_path.stat().st_mtime, (self.top_path / 'more').stat().st_mtime)

        self.watcher.changed_directory = self.top_path / "more"
        self.watcher._handle_directory_change()

        emitted_images = self._get_recent_emitted_files()
        self._file_list_count_equal(emitted_images, file_list2)


class ImageCacheTest(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.image_data_list = []
        self.image_array_mock_list = [np.random.default_rng().random(5)] * 5
        for i in range(5):
            self.image_data_list.append(mock.create_autospec(Image_Data))
            self.image_data_list[i] = mock.create_autospec(Image_Data)
            self.image_data_list[i].image_path = Path(f"abc_{i}.tif")
            self.image_data_list[i].image_modified_time = random.uniform(1000, 10000)
        self.image_cache = ImageCache()

    def test_WHEN_image_added_to_cache_THEN_image_is_in_cache(self):
        image_data = self.image_data_list[0]
        image_array_mock = self.image_array_mock_list[0]
        self.image_cache._add_to_cache(image_data, image_array_mock)
        np.testing.assert_array_equal(self.image_cache.cache_dict[image_data], image_array_mock)
        self.assertEqual(
            list(self.image_cache.cache_dict.keys())[0].image_modified_time, image_data.image_modified_time)

    def test_WHEN_remove_oldest_image_got_THEN_oldest_image_removed(self):
        for i in range(len(self.image_data_list)):
            self.image_cache._add_to_cache(self.image_data_list[i], self.image_array_mock_list[i])
        min_index = np.argmin([image.image_modified_time for image in self.image_data_list])
        self.assertEqual(self.image_cache._get_oldest_image(), self.image_data_list[min_index])
        self.image_cache._remove_oldest_image()
        self.assertNotIn(self.image_data_list[min_index], self.image_cache.cache_dict)

    def test_WHEN_image_not_in_cache_when_loaded_THEN_image_added_to_cache(self):
        self.image_cache = ImageCache()
        self.image_cache.loading_func = mock.Mock()
        self.image_cache.load_image(self.image_data_list[0])
        self.image_cache.loading_func.assert_called_once()
        self.assertIn(self.image_data_list[0], self.image_cache.cache_dict)

    def test_WHEN_image_in_cache_when_loaded_then_image_taken_from_cache(self):
        self.image_cache = ImageCache()
        self.image_cache.loading_func = mock.Mock()
        self.image_cache._add_to_cache(self.image_data_list[0], self.image_array_mock_list[0])
        image_array = self.image_cache.load_image(self.image_data_list[0])
        self.image_cache.loading_func.assert_not_called()
        np.testing.assert_array_equal(image_array, self.image_cache.cache_dict[self.image_data_list[0]])

    def test_WHEN_cache_full_THEN_loading_image_removes_oldest_image(self):
        self.image_cache = ImageCache(max_cache_size=2)
        self.image_cache._remove_oldest_image = mock.Mock()
        self.image_cache._add_to_cache(self.image_data_list[0], self.image_array_mock_list[0])
        self.image_cache._add_to_cache(self.image_data_list[1], self.image_array_mock_list[1])
        self.image_cache._add_to_cache(self.image_data_list[2], self.image_array_mock_list[2])
        self.image_cache._remove_oldest_image.assert_called_once()
