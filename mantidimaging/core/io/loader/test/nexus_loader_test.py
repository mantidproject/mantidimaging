# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

import h5py
import numpy as np

from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.io.loader.nexus_loader import _missing_data_message, _get_tomo_data, load_nexus_data, \
    TOMO_ENTRY_PATH, DATA_PATH, IMAGE_KEY_PATH
from mantidimaging.core.io.loader.nexus_loader import logger as nexus_logger

LOAD_NEXUS_FILE = "mantidimaging.core.io.loader.nexus_loader.h5py.File"


def test_missing_field_message():
    assert _missing_data_message("missing_field") == "The NeXus file does not contain the required missing_field field."


class NexusLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nexus = h5py.File("data", "w", driver="core", backing_store=False)
        self.nexus.create_group(TOMO_ENTRY_PATH)
        self.n_images = 10
        self.nexus.create_dataset(DATA_PATH, data=np.random.random((self.n_images, 10, 10)))
        self.nexus.create_dataset(IMAGE_KEY_PATH, data=np.array([1, 1, 2, 2, 0, 0, 2, 2, 1, 1]))

        self.nexus_load_patcher = mock.patch(LOAD_NEXUS_FILE)
        nexus_load_mock = self.nexus_load_patcher.start()
        nexus_load_mock.return_value = self.nexus

    def tearDown(self) -> None:
        self.nexus.close()
        self.nexus_load_patcher.stop()

    def replace_values_in_image_key(self, before: bool, prev_value: int, new_value: int):
        if before:
            self.nexus[IMAGE_KEY_PATH][:self.n_images // 2] = np.where(
                self.nexus[IMAGE_KEY_PATH][:self.n_images // 2] == prev_value, new_value,
                self.nexus[IMAGE_KEY_PATH][:self.n_images // 2])
        else:
            self.nexus[IMAGE_KEY_PATH][self.n_images // 2:] = np.where(
                self.nexus[IMAGE_KEY_PATH][self.n_images // 2:] == prev_value, new_value,
                self.nexus[IMAGE_KEY_PATH][self.n_images // 2:])

    def test_get_tomo_data(self):
        self.assertIsNotNone(_get_tomo_data(self.nexus, TOMO_ENTRY_PATH))

    def test_no_tomo_data_returns_none(self):
        del self.nexus[TOMO_ENTRY_PATH]
        self.assertIsNone(_get_tomo_data(self.nexus, TOMO_ENTRY_PATH))
        self.assertLogs(nexus_logger, level="ERROR")

    def test_load_nexus_data_returns_none_when_no_tomo_entry(self):
        del self.nexus[TOMO_ENTRY_PATH]
        self.assertIsNone(load_nexus_data("filename")[0])
        self.assertLogs(nexus_logger, level="ERROR")

    def test_load_nexus_data_returns_none_when_no_data(self):
        del self.nexus[DATA_PATH]
        self.assertIsNone(load_nexus_data("filename")[0])
        self.assertLogs(nexus_logger, level="ERROR")

    def test_load_nexus_data_returns_none_when_no_image_key(self):
        del self.nexus[IMAGE_KEY_PATH]
        self.assertIsNone(load_nexus_data("filename"))
        self.assertLogs(nexus_logger, level="ERROR")

    def test_both_missing_data_and_missing_image_key_logged(self):
        del self.nexus[DATA_PATH]
        del self.nexus[IMAGE_KEY_PATH]
        with self.assertLogs(nexus_logger, level="ERROR") as log_mock:
            self.assertIsNone(load_nexus_data("filename")[0])
            self.assertIn(DATA_PATH, log_mock.output[0])
            self.assertIn(IMAGE_KEY_PATH, log_mock.output[1])

    def test_no_projections_returns_none(self):
        self.nexus[IMAGE_KEY_PATH][:] = np.ones(self.n_images)
        with self.assertLogs(nexus_logger, level="ERROR") as log_mock:
            self.assertIsNone(load_nexus_data("filename")[0])
            self.assertIn("No projection images found in the NeXus file", log_mock.output[0])

    def test_complete_file_returns_dataset(self):
        self.assertIsInstance(load_nexus_data("filename")[0], Dataset)

    def test_no_flat_before_images_in_log(self):
        self.replace_values_in_image_key(True, 1, 2)
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            self.assertIsNone(load_nexus_data("filename")[0].flat_before)
            self.assertIn("No flat before images found in the NeXus file", log_mock.output[0])

    def test_no_flat_after_images_in_log(self):
        self.replace_values_in_image_key(False, 1, 2)
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            self.assertIsNone(load_nexus_data("filename")[0].flat_after)
            self.assertIn("No flat after images found in the NeXus file", log_mock.output[0])

    def test_no_dark_before_images_in_log(self):
        self.replace_values_in_image_key(True, 2, 1)
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            self.assertIsNone(load_nexus_data("filename")[0].dark_before)
            self.assertIn("No dark before images found in the NeXus file", log_mock.output[0])

    def test_no_dark_after_images_in_log(self):
        self.replace_values_in_image_key(False, 2, 1)
        with self.assertLogs(nexus_logger, level="INFO") as log_mock:
            self.assertIsNone(load_nexus_data("filename")[0].dark_after)
            self.assertIn("No dark after images found in the NeXus file", log_mock.output[0])

    def test_dataset_arrays_match_image_key(self):
        flat_before = self.nexus[DATA_PATH][:2]
        dark_before = self.nexus[DATA_PATH][2:4]
        sample = self.nexus[DATA_PATH][4:6]
        dark_after = self.nexus[DATA_PATH][6:8]
        flat_after = self.nexus[DATA_PATH][8:]
        dataset = load_nexus_data("filename")[0]
        np.testing.assert_array_equal(dataset.flat_before.data, flat_before)
        np.testing.assert_array_equal(dataset.dark_before.data, dark_before)
        np.testing.assert_array_equal(dataset.sample.data, sample)
        np.testing.assert_array_equal(dataset.dark_after.data, dark_after)
        np.testing.assert_array_equal(dataset.flat_after.data, flat_after)
