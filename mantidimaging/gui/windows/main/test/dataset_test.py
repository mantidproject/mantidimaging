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

    def test_cant_change_dataset_id(self):
        with self.assertRaises(Exception):
            self.dataset.id = "id"

    def test_set_flat_before(self):
        flat_before = generate_images()
        self.dataset.flat_before = flat_before
        assert flat_before is self.dataset.flat_before

    def test_set_flat_after(self):
        flat_after = generate_images()
        self.dataset.flat_after = flat_after
        assert flat_after is self.dataset.flat_after

    def test_set_dark_before(self):
        dark_before = generate_images()
        self.dataset.dark_before = dark_before
        assert dark_before is self.dataset.dark_before

    def test_set_dark_after(self):
        dark_after = generate_images()
        self.dataset.dark_after = dark_after
        assert dark_after is self.dataset.dark_after
