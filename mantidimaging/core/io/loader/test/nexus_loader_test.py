# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

import h5py
import numpy as np

from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.io.loader.nexus_loader import _missing_data_message, TOMO_ENTRY, DATA_PATH, \
    IMAGE_KEY_PATH, NexusLoader
from mantidimaging.core.io.loader.nexus_loader import logger as nexus_logger


def test_missing_field_message():
    assert _missing_data_message("missing") == "The NeXus file does not contain the required missing field."


class NexusLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nexus = h5py.File("data", "w", driver="core", backing_store=False)
        self.full_tomo_path = f"entry1/{TOMO_ENTRY}"
        self.tomo_entry = self.nexus.create_group(self.full_tomo_path)
        self.n_images = 10
        self.tomo_entry.create_dataset(DATA_PATH, data=np.random.random((self.n_images, 10, 10)), dtype="float32")
        self.tomo_entry.create_dataset(IMAGE_KEY_PATH, data=np.array([1, 1, 2, 2, 0, 0, 2, 2, 1, 1]))
        self.title = "my_data_title"
        self.tomo_entry.create_dataset("title", shape=(1, ), data=self.title.encode("UTF-8"))

        self.nexus_loader = NexusLoader()
        self.nexus_loader.nexus_file = self.nexus

        self.nexus_load_patcher = mock.patch("mantidimaging.core.io.loader.nexus_loader.h5py.File")
        nexus_load_mock = self.nexus_load_patcher.start()
        nexus_load_mock.return_value = self.nexus

    def tearDown(self) -> None:
        self.nexus.close()
        self.nexus_load_patcher.stop()

    def replace_values_in_image_key(self, before: bool, prev_value: int, new_value: int):
        """
        Changes values in the image key.
        :param before: Whether or not to change values that correspond with before images.
        :param prev_value: The previous image key value.
        :param new_value: The new image key value.
        """
        if before:
            self.tomo_entry[IMAGE_KEY_PATH][:self.n_images // 2] = np.where(
                self.tomo_entry[IMAGE_KEY_PATH][:self.n_images // 2] == prev_value, new_value,
                self.tomo_entry[IMAGE_KEY_PATH][:self.n_images // 2])
        else:
            self.tomo_entry[IMAGE_KEY_PATH][self.n_images // 2:] = np.where(
                self.tomo_entry[IMAGE_KEY_PATH][self.n_images // 2:] == prev_value, new_value,
                self.tomo_entry[IMAGE_KEY_PATH][self.n_images // 2:])

    def test_find_tomo_entry(self):
        self.assertIsNotNone(self.nexus_loader._find_tomo_entry())

    def test_find_tomo_entry_returns_none(self):
        del self.nexus[self.full_tomo_path]
        self.assertIsNone(self.nexus_loader._find_tomo_entry())

    def test_load_nexus_data_returns_none_when_no_tomo_entry(self):
        del self.nexus[self.full_tomo_path]
        with self.assertLogs(nexus_logger, level="ERROR") as log_mock:
            dataset, _, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset)
            self.assertIn(issues[0], log_mock.output[0])

    def test_load_nexus_data_returns_none_when_no_data(self):
        del self.tomo_entry[DATA_PATH]
        with self.assertLogs(nexus_logger, level="ERROR") as log_mock:
            dataset, _, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset)
            self.assertIn(issues[0], log_mock.output[0])

    def test_dataset_contains_only_sample_when_nexus_has_no_image_key(self):
        del self.tomo_entry[IMAGE_KEY_PATH]
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            projections_only, _, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(projections_only.flat_before)
            self.assertIsNone(projections_only.flat_after)
            self.assertIsNone(projections_only.dark_before)
            self.assertIsNone(projections_only.dark_after)
            self.assertIn(issues[0], log_mock.output[0])

    def test_no_projections_returns_none(self):
        self.tomo_entry[IMAGE_KEY_PATH][:] = np.ones(self.n_images)
        with self.assertLogs(nexus_logger, level="ERROR") as log_mock:
            dataset, _, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset)
            self.assertIn(issues[0], log_mock.output[0])

    def test_complete_file_returns_dataset(self):
        dataset, _, issues = self.nexus_loader.load_nexus_data("filename")
        self.assertIsInstance(dataset, Dataset)
        self.assertListEqual(issues, [])

    def test_no_flat_before_images_in_log(self):
        self.replace_values_in_image_key(True, 1, 2)
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            dataset, _, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset.flat_before)
            self.assertIn(issues[0], log_mock.output[0])

    def test_no_flat_after_images_in_log(self):
        self.replace_values_in_image_key(False, 1, 2)
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            dataset, _, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset.flat_after)
            self.assertIn(issues[0], log_mock.output[0])

    def test_no_dark_before_images_in_log(self):
        self.replace_values_in_image_key(True, 2, 1)
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            dataset, _, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset.dark_before)
            self.assertIn(issues[0], log_mock.output[0])

    def test_no_dark_after_images_in_log(self):
        self.replace_values_in_image_key(False, 2, 1)
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            dataset, _, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset.dark_after)
            self.assertIn(issues[0], log_mock.output[0])

    def test_dataset_arrays_match_image_key(self):
        flat_before = self.tomo_entry[DATA_PATH][:2]
        dark_before = self.tomo_entry[DATA_PATH][2:4]
        sample = self.tomo_entry[DATA_PATH][4:6]
        dark_after = self.tomo_entry[DATA_PATH][6:8]
        flat_after = self.tomo_entry[DATA_PATH][8:]
        dataset = self.nexus_loader.load_nexus_data("filename")[0]
        np.testing.assert_array_equal(dataset.flat_before.data, flat_before)
        np.testing.assert_array_equal(dataset.dark_before.data, dark_before)
        np.testing.assert_array_equal(dataset.sample.data, sample)
        np.testing.assert_array_equal(dataset.dark_after.data, dark_after)
        np.testing.assert_array_equal(dataset.flat_after.data, flat_after)

    def test_no_title_in_nexus_file(self):
        del self.tomo_entry["title"]
        assert self.nexus_loader.load_nexus_data("filename")[1] == "NeXus Data"

    def test_title_in_nexus_file(self):
        assert self.nexus_loader.load_nexus_data("filename")[1] == self.title

    def test_image_filenames(self):
        dataset = self.nexus_loader.load_nexus_data("filename")[0]
        assert dataset.sample.filenames[0] == "Projections " + self.title
        assert dataset.flat_before.filenames[0] == "Flat Before " + self.title
        assert dataset.dark_before.filenames[0] == "Dark Before " + self.title
        assert dataset.dark_after.filenames[0] == "Dark After " + self.title
        assert dataset.flat_after.filenames[0] == "Flat After " + self.title

    def test_projections_only_converted_to_float64(self):
        del self.tomo_entry[IMAGE_KEY_PATH]
        dataset = self.nexus_loader.load_nexus_data("filename")[0]
        assert dataset.sample.data.dtype == np.dtype("float64")

    def test_full_dataset_converted_to_float64(self):
        dataset = self.nexus_loader.load_nexus_data("filename")[0]
        assert dataset.sample.data.dtype == np.dtype("float64")
        assert dataset.flat_before.data.dtype == np.dtype("float64")
        assert dataset.dark_before.data.dtype == np.dtype("float64")
        assert dataset.dark_after.data.dtype == np.dtype("float64")
        assert dataset.flat_after.data.dtype == np.dtype("float64")
