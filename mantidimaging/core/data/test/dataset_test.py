# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock
import uuid

from mantidimaging.core.data.dataset import BaseDataset
from mantidimaging.test_helpers.unit_test_helper import generate_images


class DatasetTest(unittest.TestCase):

    def test_create_dataset(self):
        ds = BaseDataset()
        self.assertIsInstance(ds.id, uuid.UUID)
        self.assertEqual(ds.name, "")

    def test_prevent_positional_parameters(self):
        self.assertRaises(TypeError, BaseDataset, mock.Mock())

    def test_dataset_name(self):
        ds = BaseDataset(name="a_dataset")
        self.assertEqual(ds.name, "a_dataset")

    def test_add_recon(self):
        ds = BaseDataset()
        recons = [generate_images() for _ in range(3)]
        [ds.add_recon(r) for r in recons]

        for recon in recons:
            self.assertIn(recon, ds.all)
        self.assertEqual(3, len(ds.recons))

    def test_delete_recon(self):
        ds = BaseDataset()
        recons = [generate_images() for _ in range(3)]
        [ds.add_recon(r) for r in recons]

        id_to_remove = recons[-1].id
        ds.delete_stack(id_to_remove)
        self.assertNotIn(recons[-1], ds.all)

    def test_delete_failure(self):
        ds = BaseDataset()
        with self.assertRaises(KeyError):
            ds.delete_stack("nonexistent-id")

    def test_delete_all_recons(self):
        ds = BaseDataset()
        recons = [generate_images() for _ in range(3)]
        [ds.add_recon(r) for r in recons]
        ds.delete_recons()
        self.assertListEqual(ds.recons.stacks, [])

    def test_sinograms(self):
        ds = BaseDataset()
        ds.sinograms = sinograms = generate_images()
        self.assertIs(ds.sinograms, sinograms)

    def test_delete_sinograms(self):
        ds = BaseDataset()
        ds.sinograms = sinograms = generate_images()
        ds.delete_stack(sinograms.id)
        self.assertIsNone(ds.sinograms)
