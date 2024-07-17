# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
import uuid

from mantidimaging.core.data.dataset import BaseDataset
from mantidimaging.test_helpers.unit_test_helper import generate_images


class DatasetTest(unittest.TestCase):

    def test_create_dataset(self):
        ds = BaseDataset()
        self.assertIsInstance(ds.id, uuid.UUID)
        self.assertEqual(ds.name, "")

    def test_add_recon(self):
        ds = BaseDataset()
        recons = [generate_images() for _ in range(3)]
        [ds.add_recon(r) for r in recons]

        for recon in recons:
            self.assertIn(recon, ds.recons)
        self.assertEqual(3, len(ds.recons))
