# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock
import uuid

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import Dataset, _get_stack_data_type
from mantidimaging.core.utility.data_containers import ProjectionAngles, FILE_TYPES
from mantidimaging.test_helpers.unit_test_helper import generate_images, generate_standard_dataset


def _set_fake_projection_angles(image_stack: ImageStack):
    """
    Sets the private projection angles attribute.
    :param image_stack: The ImageStack object.
    """
    image_stack._projection_angles = ProjectionAngles(np.array([0, 180]))
    #image_stack.real_projection_angles.return_value = image_stack._projection_angles
    #image_stack.projection_angles.return_value = image_stack._projection_angles


class DatasetTest(unittest.TestCase):

    def test_create_dataset(self):
        ds = Dataset()
        self.assertIsInstance(ds.id, uuid.UUID)
        self.assertEqual(ds.name, "")

    def test_prevent_positional_parameters(self):
        self.assertRaises(TypeError, Dataset, mock.Mock())

    def test_dataset_name(self):
        ds = Dataset(name="a_dataset")
        self.assertEqual(ds.name, "a_dataset")

    def test_add_recon(self):
        ds = Dataset()
        recons = [generate_images() for _ in range(3)]
        [ds.add_recon(r) for r in recons]

        for recon in recons:
            self.assertIn(recon, ds.all)
        self.assertEqual(3, len(ds.recons))

    def test_delete_recon(self):
        ds = Dataset()
        recons = [generate_images() for _ in range(3)]
        [ds.add_recon(r) for r in recons]

        id_to_remove = recons[-1].id
        ds.delete_stack(id_to_remove)
        self.assertNotIn(recons[-1], ds.all)

    def test_delete_failure(self):
        ds = Dataset()
        with self.assertRaises(KeyError):
            ds.delete_stack("nonexistent-id")

    def test_delete_all_recons(self):
        ds = Dataset()
        recons = [generate_images() for _ in range(3)]
        [ds.add_recon(r) for r in recons]
        ds.delete_recons()
        self.assertListEqual(ds.recons.stacks, [])

    def test_sinograms(self):
        ds = Dataset()
        ds.sinograms = sinograms = generate_images()
        self.assertIs(ds.sinograms, sinograms)

    def test_delete_sinograms(self):
        ds = Dataset()
        ds.sinograms = sinograms = generate_images()
        ds.delete_stack(sinograms.id)
        self.assertIsNone(ds.sinograms)

    def test_stacks_in_all(self):
        image_stacks = [mock.Mock() for _ in range(3)]
        ds = Dataset(stacks=image_stacks)
        self.assertListEqual(ds.all, image_stacks)

    def test_sample_in_all(self):
        image_sample = mock.Mock(proj180deg=None)
        ds = Dataset(sample=image_sample)
        self.assertCountEqual(ds.all, [image_sample])

    def test_all_for_full_dataset(self):
        ds, image_stacks = generate_standard_dataset()
        self.assertEqual(len(ds.all), len(image_stacks))
        for image in image_stacks:
            self.assertIn(image, ds.all)

    def test_delete_stack_from_stacks_list(self):
        image_stacks = [mock.Mock() for _ in range(3)]
        ds = Dataset(stacks=image_stacks)
        prev_stacks = image_stacks.copy()
        ds.delete_stack(image_stacks[-1].id)
        self.assertListEqual(ds.all, prev_stacks[:-1])

    def test_get_stack_data_type_returns_recon(self):
        recon = generate_images()
        recon_id = recon.id
        dataset = Dataset()
        dataset.recons.append(recon)
        self.assertEqual(_get_stack_data_type(recon_id, dataset), "Recon")

    def test_get_stack_data_type_returns_images(self):
        images = generate_images()
        images_id = images.id
        dataset = Dataset(stacks=[images])
        self.assertEqual(_get_stack_data_type(images_id, dataset), "Images")

    def test_attribute_not_set_returns_none(self):
        sample = mock.Mock()
        dataset = Dataset(sample=sample)

        self.assertIsNone(dataset.flat_before)
        self.assertIsNone(dataset.flat_after)
        self.assertIsNone(dataset.dark_before)
        self.assertIsNone(dataset.dark_after)

    def test_set_flat_before(self):
        sample = mock.Mock()
        dataset = Dataset(sample=sample)
        flat_before = mock.Mock(id="1234")
        dataset.flat_before = flat_before
        self.assertIs(flat_before, dataset.flat_before)
        self.assertIn("1234", dataset)

    def test_all_images_ids(self):
        ds, images = generate_standard_dataset()
        self.assertCountEqual(ds.all_image_ids, [image.id for image in images])

    def test_nexus_stack_order(self):
        ds, _ = generate_standard_dataset()
        self.assertListEqual(ds._nexus_stack_order,
                             [ds.dark_before, ds.flat_before, ds.sample, ds.flat_after, ds.dark_after])

    def test_nexus_arrays(self):
        ds, _ = generate_standard_dataset()
        self.assertListEqual(
            ds.nexus_arrays,
            [ds.dark_before.data, ds.flat_before.data, ds.sample.data, ds.flat_after.data, ds.dark_after.data])

    def test_image_keys(self):
        ds, images = generate_standard_dataset()

        self.assertListEqual(ds.image_keys, [2, 2, 1, 1, 0, 0, 1, 1, 2, 2])

    def test_missing_dark_before_image_keys(self):
        ds, images = generate_standard_dataset()
        ds.dark_before = None

        self.assertListEqual(ds.image_keys, [1, 1, 0, 0, 1, 1, 2, 2])

    def test_missing_flat_before_image_keys(self):
        ds, images = generate_standard_dataset()
        ds.flat_before = None

        self.assertListEqual(ds.image_keys, [2, 2, 0, 0, 1, 1, 2, 2])

    def test_missing_flat_after_image_keys(self):
        ds, images = generate_standard_dataset()
        ds.flat_after = None

        self.assertListEqual(ds.image_keys, [2, 2, 1, 1, 0, 0, 2, 2])

    def test_missing_dark_after_image_keys(self):
        ds, images = generate_standard_dataset()
        ds.dark_after = None

        self.assertListEqual(ds.image_keys, [2, 2, 1, 1, 0, 0, 1, 1])

    def test_no_sample_image_keys(self):
        ds, images = generate_standard_dataset()
        ds.sample = None
        with self.assertRaises(RuntimeError):
            _ = ds.image_keys

    def test_rotation_angles(self):
        ds, images = generate_standard_dataset()
        for stack in images:
            _set_fake_projection_angles(stack)
        assert np.array_equal(ds.nexus_rotation_angles, [
            ds.dark_before.projection_angles().value,
            ds.flat_before.projection_angles().value,
            ds.sample.projection_angles().value,
            ds.flat_after.projection_angles().value,
            ds.dark_after.projection_angles().value
        ])

    def test_incomplete_nexus_rotation_angles(self):
        ds, _ = generate_standard_dataset()
        expected_list = []
        for stack in ds._nexus_stack_order:
            expected_list.append(np.zeros(stack.num_images))

        assert np.array_equal(expected_list, ds.nexus_rotation_angles)

    def test_partially_incomplete_nexus_rotation_angles(self):
        ds, _ = generate_standard_dataset()

        _set_fake_projection_angles(ds.dark_before)
        _set_fake_projection_angles(ds.flat_before)
        _set_fake_projection_angles(ds.dark_after)
        expected_list = [
            ds.dark_before.projection_angles().value,
            ds.flat_before.projection_angles().value,
            np.zeros(ds.sample.num_images),
            np.zeros(ds.flat_after.num_images),
            ds.dark_after.projection_angles().value
        ]

        assert np.array_equal(expected_list, ds.nexus_rotation_angles)

    def test_delete_sample(self):
        ds, images = generate_standard_dataset()
        ds.delete_stack(images[0].id)
        self.assertIsNone(ds.sample)

    def test_delete_flat_before(self):
        ds, images = generate_standard_dataset()
        ds.delete_stack(images[1].id)
        self.assertIsNone(ds.flat_before)

    def test_delete_flat_after(self):
        ds, images = generate_standard_dataset()
        ds.delete_stack(images[2].id)
        self.assertIsNone(ds.flat_after)

    def test_delete_dark_before(self):
        ds, images = generate_standard_dataset()
        ds.delete_stack(images[3].id)
        self.assertIsNone(ds.dark_before)

    def test_delete_dark_after(self):
        ds, images = generate_standard_dataset()
        ds.delete_stack(images[4].id)
        self.assertIsNone(ds.dark_after)

    def test_set_stack_by_type_sample(self):
        ds = Dataset()
        sample = mock.Mock()
        ds.set_stack(FILE_TYPES.SAMPLE, sample)

        self.assertEqual(ds.sample, sample)

    def test_set_stack_by_type_flat_before(self):
        ds = Dataset()
        stack = mock.Mock()
        ds.set_stack(FILE_TYPES.FLAT_BEFORE, stack)

        self.assertEqual(ds.flat_before, stack)

    def test_set_stack_by_type_180(self):
        ds = Dataset()
        sample = mock.Mock()
        stack = mock.Mock()
        ds.set_stack(FILE_TYPES.SAMPLE, sample)
        ds.set_stack(FILE_TYPES.PROJ_180, stack)

        self.assertEqual(ds.proj180deg, stack)

    def test_processed_is_true(self):
        ds = Dataset(sample=generate_images())
        ds.sample.record_operation("", "")
        self.assertTrue(ds.is_processed)

    def test_processed_is_false(self):
        ds = Dataset(sample=generate_images())
        self.assertFalse(ds.is_processed)
