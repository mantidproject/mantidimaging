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

    def test_delete_stack_from_stacks_list(self):
        prev_stacks = self.image_stacks.copy()
        self.stack_dataset.delete_stack(self.image_stacks[-1].id)
        self.assertListEqual(self.stack_dataset.all, prev_stacks[:-1])

    def test_delete_stack_from_recons_list(self):
        recons = [generate_images() for _ in range(2)]
        self.stack_dataset.recons = recons.copy()

        id_to_remove = recons[-1].id
        self.stack_dataset.delete_stack(id_to_remove)
        self.assertNotIn(recons[-1], self.stack_dataset.all)

    def test_delete_stack_failure(self):
        with self.assertRaises(KeyError):
            self.stack_dataset.delete_stack("nonexistent-id")

    def test_all_ids(self):
        self.assertListEqual(self.stack_dataset.all_image_ids, [image_stack.id for image_stack in self.image_stacks])
