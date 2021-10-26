import unittest

from mantidimaging.core.data import Images
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

    def test_images_returned(self):
        self.assertIsInstance(self.dataset.sample, Images)
        self.assertIsInstance(self.dataset.flat_before, Images)
        self.assertIsInstance(self.dataset.flat_after, Images)
        self.assertIsInstance(self.dataset.dark_before, Images)
        self.assertIsInstance(self.dataset.dark_after, Images)

    def test_attribute_not_set_returns_none(self):
        sample = generate_images()
        dataset = Dataset(sample)

        self.assertIsNone(dataset.flat_before)
        self.assertIsNone(dataset.flat_after)
        self.assertIsNone(dataset.dark_before)
        self.assertIsNone(dataset.dark_after)
