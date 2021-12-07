# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest

from mantidimaging.core.data.dataset import StackDataset
from mantidimaging.test_helpers.unit_test_helper import generate_images


class StackDatasetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.image_stacks = [generate_images() for _ in range(3)]
        self.stack_dataset = StackDataset(self.image_stacks)

    def test_all(self):
        self.assertListEqual(self.stack_dataset.all, self.image_stacks)

    def test_delete_stack(self):
        prev_stacks = self.image_stacks.copy()
        self.stack_dataset.delete_stack(self.image_stacks[-1].id)
        self.assertListEqual(self.stack_dataset.all, prev_stacks[:-1])
