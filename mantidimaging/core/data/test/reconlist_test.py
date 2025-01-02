# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
import uuid

from mantidimaging.core.data.reconlist import ReconList
from mantidimaging.test_helpers.unit_test_helper import generate_images


class ReconListTest(unittest.TestCase):

    def setUp(self) -> None:
        self.recon_list = ReconList([generate_images() for _ in range(3)])

    def test_recon_list_id(self):
        self.assertIsInstance(self.recon_list.id, uuid.UUID)

    def test_recon_list_ids(self):
        ids = [recon.id for recon in self.recon_list.data]
        self.assertListEqual(self.recon_list.ids, ids)
