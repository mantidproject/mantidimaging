# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest

from numpy import array_equal

from mantidimaging.core.data.dataset import StrictDataset, _delete_stack_error_message, MixedDataset
from mantidimaging.test_helpers.unit_test_helper import generate_images


def test_delete_stack_error_message():
    assert _delete_stack_error_message("stack-id") == "Unable to delete stack: Images with ID stack-id not present in" \
                                                      " dataset."


class DatasetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.images = [generate_images() for _ in range(5)]
        self.strict_dataset = StrictDataset(sample=self.images[0],
                                            flat_before=self.images[1],
                                            flat_after=self.images[2],
                                            dark_before=self.images[3],
                                            dark_after=self.images[4])
        self.mixed_dataset = MixedDataset([generate_images()])

    def test_attribute_not_set_returns_none(self):
        sample = generate_images()
        dataset = StrictDataset(sample)

        self.assertIsNone(dataset.flat_before)
        self.assertIsNone(dataset.flat_after)
        self.assertIsNone(dataset.dark_before)
        self.assertIsNone(dataset.dark_after)

    def test_replace_success(self):
        sample_id = self.images[0].id
        new_sample_data = generate_images().data
        self.strict_dataset.replace(sample_id, new_sample_data)
        assert array_equal(self.strict_dataset.sample.data, new_sample_data)

    def test_replace_failure(self):
        with self.assertRaises(KeyError):
            self.strict_dataset.replace("nonexistent-id", generate_images().data)

    def test_cant_change_dataset_id(self):
        with self.assertRaises(Exception):
            self.strict_dataset.id = "id"

    def test_set_flat_before(self):
        flat_before = generate_images()
        self.strict_dataset.flat_before = flat_before
        assert flat_before is self.strict_dataset.flat_before

    def test_set_flat_after(self):
        flat_after = generate_images()
        self.strict_dataset.flat_after = flat_after
        assert flat_after is self.strict_dataset.flat_after

    def test_set_dark_before(self):
        dark_before = generate_images()
        self.strict_dataset.dark_before = dark_before
        assert dark_before is self.strict_dataset.dark_before

    def test_set_dark_after(self):
        dark_after = generate_images()
        self.strict_dataset.dark_after = dark_after
        assert dark_after is self.strict_dataset.dark_after

    def test_all(self):
        self.assertListEqual(self.strict_dataset.all, self.images)

    def test_all_images_ids(self):
        self.assertListEqual(self.strict_dataset.all_image_ids, [images.id for images in self.images])

    def test_contains_returns_true(self):
        assert self.images[2].id in self.strict_dataset

    def test_contains_returns_false(self):
        assert not generate_images().id in self.strict_dataset

    def test_delete_sample(self):
        self.strict_dataset.delete_stack(self.images[0].id)
        self.assertIsNone(self.strict_dataset.sample)

    def test_delete_flat_before(self):
        self.strict_dataset.delete_stack(self.images[1].id)
        self.assertIsNone(self.strict_dataset.flat_before)

    def test_delete_flat_after(self):
        self.strict_dataset.delete_stack(self.images[2].id)
        self.assertIsNone(self.strict_dataset.flat_after)

    def test_delete_dark_before(self):
        self.strict_dataset.delete_stack(self.images[3].id)
        self.assertIsNone(self.strict_dataset.dark_before)

    def test_delete_dark_after(self):
        self.strict_dataset.delete_stack(self.images[4].id)
        self.assertIsNone(self.strict_dataset.dark_after)

    def test_delete_recon(self):
        recons = [generate_images() for _ in range(2)]
        self.strict_dataset.recons = recons.copy()

        id_to_remove = recons[-1].id
        self.strict_dataset.delete_stack(id_to_remove)
        self.assertNotIn(recons[-1], self.strict_dataset.all)

    def test_delete_failure(self):
        with self.assertRaises(KeyError):
            self.strict_dataset.delete_stack("nonexistent-id")

    def test_name(self):
        self.strict_dataset.name = dataset_name = "name"
        assert self.strict_dataset.name == dataset_name

    def test_set_180(self):
        _180 = generate_images((1, 200, 200))
        self.strict_dataset.proj180deg = _180
        assert self.strict_dataset.proj180deg is _180
        assert self.strict_dataset.sample.proj180deg is _180

    def test_remove_180(self):
        _180 = generate_images((1, 200, 200))
        self.strict_dataset.proj180deg = _180
        self.strict_dataset.delete_stack(_180.id)
        self.assertIsNone(self.strict_dataset.proj180deg)
        self.assertIsNone(self.strict_dataset.sample.proj180deg)

    def test_sinograms(self):
        self.strict_dataset.sinograms = sinograms = generate_images()
        self.assertIs(self.strict_dataset.sinograms, sinograms)

    def test_delete_sinograms(self):
        self.strict_dataset.sinograms = sinograms = generate_images()
        self.strict_dataset.delete_stack(sinograms.id)
        self.assertIsNone(self.strict_dataset.sinograms)

    def test_sinograms_in_mixed_dataset_all(self):
        self.assertListEqual(self.mixed_dataset._stacks, self.mixed_dataset.all)
        self.mixed_dataset.sinograms = sinograms = generate_images()
        self.assertListEqual(self.mixed_dataset._stacks + [sinograms], self.mixed_dataset.all)
