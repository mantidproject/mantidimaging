# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

import h5py
import numpy as np

from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.io.loader.nexus_loader import _missing_data_message, TOMO_ENTRY_PATH, DATA_PATH, \
    IMAGE_KEY_PATH, NexusLoader
from mantidimaging.core.io.loader.nexus_loader import logger as nexus_logger


def test_missing_field_message():
    assert _missing_data_message("missing") == "The NeXus file does not contain the required missing field."


class NexusLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nexus = h5py.File("data", "w", driver="core", backing_store=False)
        self.nexus.create_group(TOMO_ENTRY_PATH)
        self.n_images = 10
        self.nexus.create_dataset(DATA_PATH, data=np.random.random((self.n_images, 10, 10)))
        self.nexus.create_dataset(IMAGE_KEY_PATH, data=np.array([1, 1, 2, 2, 0, 0, 2, 2, 1, 1]))

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
            self.nexus[IMAGE_KEY_PATH][:self.n_images // 2] = np.where(
                self.nexus[IMAGE_KEY_PATH][:self.n_images // 2] == prev_value, new_value,
                self.nexus[IMAGE_KEY_PATH][:self.n_images // 2])
        else:
            self.nexus[IMAGE_KEY_PATH][self.n_images // 2:] = np.where(
                self.nexus[IMAGE_KEY_PATH][self.n_images // 2:] == prev_value, new_value,
                self.nexus[IMAGE_KEY_PATH][self.n_images // 2:])

    def test_get_tomo_data(self):
        self.assertIsNotNone(self.nexus_loader._get_tomo_data(TOMO_ENTRY_PATH))

    def test_no_tomo_data_returns_none(self):
        del self.nexus[TOMO_ENTRY_PATH]
        self.assertIsNone(self.nexus_loader._get_tomo_data(TOMO_ENTRY_PATH))

    def test_load_nexus_data_returns_none_when_no_tomo_entry(self):
        del self.nexus[TOMO_ENTRY_PATH]
        with self.assertLogs(nexus_logger, level="ERROR") as log_mock:
            dataset, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset)
            self.assertIn(issues[0], log_mock.output[0])

    def test_load_nexus_data_returns_none_when_no_data(self):
        del self.nexus[DATA_PATH]
        with self.assertLogs(nexus_logger, level="ERROR") as log_mock:
            dataset, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset)
            self.assertIn(issues[0], log_mock.output[0])

    def test_dataset_contains_only_sample_when_nexus_has_no_image_key(self):
        del self.nexus[IMAGE_KEY_PATH]
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            projections_only, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(projections_only.flat_before)
            self.assertIsNone(projections_only.flat_after)
            self.assertIsNone(projections_only.dark_before)
            self.assertIsNone(projections_only.dark_after)
            self.assertIn(issues[0], log_mock.output[0])

    def test_no_projections_returns_none(self):
        self.nexus[IMAGE_KEY_PATH][:] = np.ones(self.n_images)
        with self.assertLogs(nexus_logger, level="ERROR") as log_mock:
            dataset, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset)
            self.assertIn(issues[0], log_mock.output[0])

    def test_complete_file_returns_dataset(self):
        dataset, issues = self.nexus_loader.load_nexus_data("filename")
        self.assertIsInstance(dataset, Dataset)
        self.assertListEqual(issues, [])

    def test_no_flat_before_images_in_log(self):
        self.replace_values_in_image_key(True, 1, 2)
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            dataset, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset.flat_before)
            self.assertIn(issues[0], log_mock.output[0])

    def test_no_flat_after_images_in_log(self):
        self.replace_values_in_image_key(False, 1, 2)
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            dataset, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset.flat_after)
            self.assertIn(issues[0], log_mock.output[0])

    def test_no_dark_before_images_in_log(self):
        self.replace_values_in_image_key(True, 2, 1)
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            dataset, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset.dark_before)
            self.assertIn(issues[0], log_mock.output[0])

    def test_no_dark_after_images_in_log(self):
        self.replace_values_in_image_key(False, 2, 1)
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            dataset, issues = self.nexus_loader.load_nexus_data("filename")
            self.assertIsNone(dataset.dark_after)
            self.assertIn(issues[0], log_mock.output[0])

    def test_dataset_arrays_match_image_key(self):
        flat_before = self.nexus[DATA_PATH][:2]
        dark_before = self.nexus[DATA_PATH][2:4]
        sample = self.nexus[DATA_PATH][4:6]
        dark_after = self.nexus[DATA_PATH][6:8]
        flat_after = self.nexus[DATA_PATH][8:]
        dataset = self.nexus_loader.load_nexus_data("filename")[0]
        np.testing.assert_array_equal(dataset.flat_before.data, flat_before)
        np.testing.assert_array_equal(dataset.dark_before.data, dark_before)
        np.testing.assert_array_equal(dataset.sample.data, sample)
        np.testing.assert_array_equal(dataset.dark_after.data, dark_after)
        np.testing.assert_array_equal(dataset.flat_after.data, flat_after)
