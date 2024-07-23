# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import StrictDataset, _delete_stack_error_message, _image_key_list, \
    _get_stack_data_type
from mantidimaging.test_helpers.unit_test_helper import generate_images


def test_delete_stack_error_message():
    assert _delete_stack_error_message("stack-id") == "Unable to delete stack: ImageStack with ID stack-id not " \
                                                      "present in dataset."


def test_image_key_list():
    assert _image_key_list(2, 5) == [2, 2, 2, 2, 2]


def _set_fake_projection_angles(image_stack: ImageStack):
    """
    Sets the private projection angles attribute.
    :param image_stack: The ImageStack object.
    """
    image_stack._projection_angles = image_stack.projection_angles()


class StrictDatasetTest(unittest.TestCase):

    def setUp(self) -> None:
        self.images = [generate_images() for _ in range(5)]
        self.strict_dataset = StrictDataset(sample=self.images[0],
                                            flat_before=self.images[1],
                                            flat_after=self.images[2],
                                            dark_before=self.images[3],
                                            dark_after=self.images[4])

    def test_attribute_not_set_returns_none(self):
        sample = generate_images()
        dataset = StrictDataset(sample)

        self.assertIsNone(dataset.flat_before)
        self.assertIsNone(dataset.flat_after)
        self.assertIsNone(dataset.dark_before)
        self.assertIsNone(dataset.dark_after)

    def test_cant_change_dataset_id(self):
        with self.assertRaises(AttributeError):
            self.strict_dataset.id = "id"

    def test_set_flat_before(self):
        flat_before = generate_images()
        self.strict_dataset.flat_before = flat_before
        self.assertIs(flat_before, self.strict_dataset.flat_before)

    def test_set_flat_after(self):
        flat_after = generate_images()
        self.strict_dataset.flat_after = flat_after
        self.assertIs(flat_after, self.strict_dataset.flat_after)

    def test_set_dark_before(self):
        dark_before = generate_images()
        self.strict_dataset.dark_before = dark_before
        self.assertIs(dark_before, self.strict_dataset.dark_before)

    def test_set_dark_after(self):
        dark_after = generate_images()
        self.strict_dataset.dark_after = dark_after
        self.assertIs(dark_after, self.strict_dataset.dark_after)

    def test_all(self):
        self.assertListEqual(self.strict_dataset.all, self.images)

    def test_all_images_ids(self):
        self.assertListEqual(self.strict_dataset.all_image_ids, [images.id for images in self.images])

    def test_contains_returns_true(self):
        self.assertIn(self.images[2].id, self.strict_dataset)

    def test_contains_returns_false(self):
        self.assertNotIn(generate_images().id, self.strict_dataset)

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
        [self.strict_dataset.add_recon(generate_images()) for _ in range(3)]
        recons = self.strict_dataset.recons.copy()

        id_to_remove = recons[-1].id
        self.strict_dataset.delete_stack(id_to_remove)
        self.assertNotIn(recons[-1], self.strict_dataset.all)

    def test_delete_failure(self):
        with self.assertRaises(KeyError):
            self.strict_dataset.delete_stack("nonexistent-id")

    def test_name(self):
        self.strict_dataset.name = dataset_name = "name"
        self.assertEqual(self.strict_dataset.name, dataset_name)

    def test_default_name_from_image(self):
        mock_sample = mock.create_autospec(ImageStack)
        mock_sample.name = "image_name"
        ds = StrictDataset(sample=mock_sample)
        self.assertEqual(ds.name, "image_name")

    def test_set_180(self):
        _180 = generate_images((1, 200, 200))
        self.strict_dataset.proj180deg = _180
        self.assertIs(self.strict_dataset.proj180deg, _180)
        self.assertIs(self.strict_dataset.sample.proj180deg, _180)

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

    def test_delete_all_recons(self):
        [self.strict_dataset.add_recon(generate_images()) for _ in range(3)]
        self.strict_dataset.delete_recons()
        self.assertListEqual(self.strict_dataset.recons.stacks, [])

    def test_nexus_stack_order(self):
        self.assertListEqual(self.strict_dataset._nexus_stack_order, [
            self.strict_dataset.dark_before, self.strict_dataset.flat_before, self.strict_dataset.sample,
            self.strict_dataset.flat_after, self.strict_dataset.dark_after
        ])

    def test_nexus_arrays(self):
        self.assertListEqual(self.strict_dataset.nexus_arrays, [
            self.strict_dataset.dark_before.data, self.strict_dataset.flat_before.data, self.strict_dataset.sample.data,
            self.strict_dataset.flat_after.data, self.strict_dataset.dark_after.data
        ])

    def test_image_keys(self):
        self.strict_dataset.dark_before = generate_images((2, 5, 5))
        self.strict_dataset.flat_before = generate_images((2, 5, 5))
        self.strict_dataset.sample = generate_images((2, 5, 5))
        self.strict_dataset.flat_after = generate_images((2, 5, 5))
        self.strict_dataset.dark_after = generate_images((2, 5, 5))

        self.assertListEqual(self.strict_dataset.image_keys, [2, 2, 1, 1, 0, 0, 1, 1, 2, 2])

    def test_missing_dark_before_image_keys(self):
        self.strict_dataset.dark_before = None
        self.strict_dataset.flat_before = generate_images((2, 5, 5))
        self.strict_dataset.sample = generate_images((2, 5, 5))
        self.strict_dataset.flat_after = generate_images((2, 5, 5))
        self.strict_dataset.dark_after = generate_images((2, 5, 5))

        self.assertListEqual(self.strict_dataset.image_keys, [1, 1, 0, 0, 1, 1, 2, 2])

    def test_missing_flat_before_image_keys(self):
        self.strict_dataset.dark_before = generate_images((2, 5, 5))
        self.strict_dataset.flat_before = None
        self.strict_dataset.sample = generate_images((2, 5, 5))
        self.strict_dataset.flat_after = generate_images((2, 5, 5))
        self.strict_dataset.dark_after = generate_images((2, 5, 5))

        self.assertListEqual(self.strict_dataset.image_keys, [2, 2, 0, 0, 1, 1, 2, 2])

    def test_missing_flat_after_image_keys(self):
        self.strict_dataset.dark_before = generate_images((2, 5, 5))
        self.strict_dataset.flat_before = generate_images((2, 5, 5))
        self.strict_dataset.sample = generate_images((2, 5, 5))
        self.strict_dataset.flat_after = None
        self.strict_dataset.dark_after = generate_images((2, 5, 5))

        self.assertListEqual(self.strict_dataset.image_keys, [2, 2, 1, 1, 0, 0, 2, 2])

    def test_missing_dark_after_image_keys(self):
        self.strict_dataset.dark_before = generate_images((2, 5, 5))
        self.strict_dataset.flat_before = generate_images((2, 5, 5))
        self.strict_dataset.sample = generate_images((2, 5, 5))
        self.strict_dataset.flat_after = generate_images((2, 5, 5))
        self.strict_dataset.dark_after = None

        self.assertListEqual(self.strict_dataset.image_keys, [2, 2, 1, 1, 0, 0, 1, 1])

    def test_no_sample_image_keys(self):
        self.strict_dataset.sample = None
        with self.assertRaises(RuntimeError):
            _ = self.strict_dataset.image_keys

    def test_rotation_angles(self):
        for stack in self.strict_dataset._nexus_stack_order:
            _set_fake_projection_angles(stack)
        assert np.array_equal(self.strict_dataset.nexus_rotation_angles, [
            self.strict_dataset.dark_before.projection_angles().value,
            self.strict_dataset.flat_before.projection_angles().value,
            self.strict_dataset.sample.projection_angles().value,
            self.strict_dataset.flat_after.projection_angles().value,
            self.strict_dataset.dark_after.projection_angles().value
        ])

    def test_incomplete_nexus_rotation_angles(self):
        expected_list = []
        for stack in self.strict_dataset._nexus_stack_order:
            expected_list.append(np.zeros(stack.num_images))

        assert np.array_equal(expected_list, self.strict_dataset.nexus_rotation_angles)

    def test_partially_incomplete_nexus_rotation_angles(self):
        _set_fake_projection_angles(self.strict_dataset.dark_before)
        _set_fake_projection_angles(self.strict_dataset.flat_before)
        _set_fake_projection_angles(self.strict_dataset.dark_after)
        expected_list = [
            self.strict_dataset.dark_before.projection_angles().value,
            self.strict_dataset.flat_before.projection_angles().value,
            np.zeros(self.strict_dataset.sample.num_images),
            np.zeros(self.strict_dataset.flat_after.num_images),
            self.strict_dataset.dark_after.projection_angles().value
        ]

        assert np.array_equal(expected_list, self.strict_dataset.nexus_rotation_angles)

    def test_get_stack_data_type_returns_sample(self):
        sample = generate_images()
        sample_id = sample.id
        dataset = StrictDataset(sample)
        self.assertEqual(_get_stack_data_type(sample_id, dataset), "Sample")

    def test_get_stack_data_type_returns_flat_before(self):
        flat_before = generate_images()
        flat_before_id = flat_before.id
        dataset = StrictDataset(sample=generate_images(), flat_before=flat_before)
        self.assertEqual(_get_stack_data_type(flat_before_id, dataset), "Flat Before")

    def test_get_stack_data_type_returns_flat_after(self):
        flat_after = generate_images()
        flat_after_id = flat_after.id
        dataset = StrictDataset(sample=generate_images(), flat_after=flat_after)
        self.assertEqual(_get_stack_data_type(flat_after_id, dataset), "Flat After")

    def test_get_stack_data_type_returns_dark_before(self):
        dark_before = generate_images()
        dark_before_id = dark_before.id
        dataset = StrictDataset(sample=generate_images(), dark_before=dark_before)
        self.assertEqual(_get_stack_data_type(dark_before_id, dataset), "Dark Before")

    def test_get_stack_data_type_returns_dark_after(self):
        dark_after = generate_images()
        dark_after_id = dark_after.id
        dataset = StrictDataset(sample=generate_images(), dark_after=dark_after)
        self.assertEqual(_get_stack_data_type(dark_after_id, dataset), "Dark After")

    def test_get_stack_data_type_raises(self):
        empty_ds = StrictDataset(generate_images())
        with self.assertRaises(RuntimeError):
            _get_stack_data_type("bad-id", empty_ds)

    def test_processed_is_true(self):
        ds = StrictDataset(generate_images())
        ds.sample.record_operation("", "")
        self.assertTrue(ds.is_processed)

    def test_processed_is_false(self):
        ds = StrictDataset(generate_images())
        self.assertFalse(ds.is_processed)
