import unittest
from unittest import mock

import h5py

from mantidimaging.core.io.loader.nexus_loader import _missing_field_message, get_tomo_data, load_nexus_data


def test_missing_field_message():
    assert _missing_field_message(
        "missing_field") == "The NeXus file does not contain the required missing_field field."


class NexusLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nexus = h5py.File("data", "w", driver="core", backing_store=False)
        self.nexus.create_group("/entry1/tomo_entry")

    def tearDown(self) -> None:
        self.nexus.close()

    def test_get_tomo_data(self):
        self.assertIsNotNone(get_tomo_data(self.nexus, "/entry1/tomo_entry"))

    def test_no_tomo_data_returns_none(self):
        del self.nexus["/entry1/tomo_entry"]
        self.assertIsNone(get_tomo_data(self.nexus, "/entry1/tomo_entry"))

    def test_load_nexus_data_returns_none_when_there_is_no_tomo_entry_in_file(self):
        del self.nexus["/entry1/tomo_entry"]
        with mock.patch("mantidimaging.core.io.loader.nexus_loader._load_nexus_file", return_value=self.nexus):
            self.assertIsNone(load_nexus_data("filename"))
