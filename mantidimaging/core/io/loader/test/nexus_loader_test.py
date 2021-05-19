import unittest
from unittest import mock

import h5py
import numpy as np

from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.io.loader.nexus_loader import _missing_data_message, get_tomo_data, load_nexus_data, \
    TOMO_ENTRY_PATH, DATA_PATH, IMAGE_KEY_PATH
from mantidimaging.core.io.loader.nexus_loader import logger as nexus_logger

LOAD_NEXUS_FILE = "mantidimaging.core.io.loader.nexus_loader._load_nexus_file"


def test_missing_field_message():
    assert _missing_data_message("missing_field") == "The NeXus file does not contain the required missing_field field."


class NexusLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nexus = h5py.File("data", "w", driver="core", backing_store=False)
        self.nexus.create_group(TOMO_ENTRY_PATH)
        self.n_images = 10
        self.nexus.create_dataset(DATA_PATH, data=np.random.random((self.n_images, 10, 10)))
        self.nexus.create_dataset(IMAGE_KEY_PATH, data=np.array([1, 1, 2, 2, 0, 0, 2, 2, 1, 1], dtype=int))

    def tearDown(self) -> None:
        self.nexus.close()

    def test_get_tomo_data(self):
        self.assertIsNotNone(get_tomo_data(self.nexus, TOMO_ENTRY_PATH))

    def test_no_tomo_data_returns_none(self):
        del self.nexus[TOMO_ENTRY_PATH]
        self.assertIsNone(get_tomo_data(self.nexus, TOMO_ENTRY_PATH))
        self.assertLogs(nexus_logger, level="ERROR")

    def test_load_nexus_data_returns_none_when_no_tomo_entry(self):
        del self.nexus[TOMO_ENTRY_PATH]
        with mock.patch(LOAD_NEXUS_FILE, return_value=self.nexus):
            self.assertIsNone(load_nexus_data("filename"))
            self.assertLogs(nexus_logger, level="ERROR")

    def test_load_nexus_data_returns_none_when_no_data(self):
        del self.nexus[DATA_PATH]
        with mock.patch(LOAD_NEXUS_FILE, return_value=self.nexus):
            self.assertIsNone(load_nexus_data("filename"))
            self.assertLogs(nexus_logger, level="ERROR")

    def test_load_nexus_data_returns_none_when_no_image_key(self):
        del self.nexus[IMAGE_KEY_PATH]
        with mock.patch(LOAD_NEXUS_FILE, return_value=self.nexus):
            self.assertIsNone(load_nexus_data("filename"))
            self.assertLogs(nexus_logger, level="ERROR")

    def test_both_missing_data_and_missing_image_key_logged(self):
        del self.nexus[DATA_PATH]
        del self.nexus[IMAGE_KEY_PATH]
        with mock.patch(LOAD_NEXUS_FILE, return_value=self.nexus):
            with self.assertLogs(nexus_logger, level="ERROR") as log_mock:
                load_nexus_data("filename")
                self.assertIn(DATA_PATH, log_mock.output[0])
                self.assertIn(IMAGE_KEY_PATH, log_mock.output[1])

    def test_no_projections_returns_none(self):
        self.nexus[IMAGE_KEY_PATH][:] = np.ones(self.n_images)
        with mock.patch(LOAD_NEXUS_FILE, return_value=self.nexus):
            with self.assertLogs(nexus_logger, level="ERROR") as log_mock:
                self.assertIsNone(load_nexus_data("filename"))
                self.assertIn("No sample images found in NeXus file", log_mock.output[0])

    def test_complete_file_returns_dataset(self):
        with mock.patch(LOAD_NEXUS_FILE, return_value=self.nexus):
            self.assertIsInstance(load_nexus_data("filename"), Dataset)
