import unittest

from mantidimaging.core.data.dataset import Dataset
from mantidimaging.test_helpers.unit_test_helper import generate_images


class DatasetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.images = [generate_images() for _ in range(5)]
        self.dataset = Dataset(*self.images)

    def test_delete_flat_before(self):
        self.images.pop(1)
        self.assertIsNone(self.dataset.flat_before)

    def test_delete_flat_after(self):
        self.images.pop(2)
        self.assertIsNone(self.dataset.flat_after)

    def test_delete_dark_before(self):
        self.images.pop(3)
        self.assertIsNone(self.dataset.dark_before)

    def test_delete_dark_after(self):
        self.images.pop(4)
        self.assertIsNone(self.dataset.dark_after)
        