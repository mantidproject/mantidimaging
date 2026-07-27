# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
import uuid

from mantidimaging.gui.windows.main.presenter import StackId
from mantidimaging.gui.windows.main.image_save_dialog import sort_by_tomo_and_recon, ImageSaveDialog
from mantidimaging.test_helpers.start_qapplication import start_qapplication


class ImageSaveDialogTest(unittest.TestCase):

    def test_sort_stack_names_order(self):
        stack_list = [
            StackId(uuid.uuid4(), "Stack 1"),
            StackId(uuid.uuid4(), "Stack 2"),
            StackId(uuid.uuid4(), "Stack 3"),
            StackId(uuid.uuid4(), "Tomo"),
            StackId(uuid.uuid4(), "Recon"),
        ]
        new_names = sorted(stack_list, key=sort_by_tomo_and_recon)

        self.assertEqual("Recon", new_names[0].name)
        self.assertEqual("Tomo", new_names[1].name)


@start_qapplication
class SaveDialogQtTest(unittest.TestCase):

    def test_init_sorts_stack_list_correctly(self):
        stack_list = [
            StackId(uuid.uuid4(), "Stack 1"),
            StackId(uuid.uuid4(), "Stack 2"),
            StackId(uuid.uuid4(), "Stack 3"),
            StackId(uuid.uuid4(), "Stack Tomo"),
            StackId(uuid.uuid4(), "Stack Recon"),
        ]
        mwsd = ImageSaveDialog(None, stack_list)

        # the Recon stack is top choice
        self.assertEqual(mwsd.stack_uuids[0], stack_list[4].id)
        # the Tomo stack is 2nd choice
        self.assertEqual(mwsd.stack_uuids[1], stack_list[3].id)

    def test_init_uses_selected_stack_as_default(self):
        stack_list = [
            StackId(uuid.uuid4(), "Stack 1"),
            StackId(uuid.uuid4(), "Stack 2"),
            StackId(uuid.uuid4(), "Stack 3"),
        ]
        selected_stack_id = stack_list[1].id
        mwsd = ImageSaveDialog(None, stack_list, selected_stack_uuid=selected_stack_id)

        self.assertEqual(mwsd.stackNames.currentIndex(), 1)
        self.assertEqual(mwsd.stack_uuids[mwsd.stackNames.currentIndex()], selected_stack_id)

    def test_init_falls_back_to_existing_default_when_selected_stack_not_present(self):
        stack_list = [
            StackId(uuid.uuid4(), "Stack 1"),
            StackId(uuid.uuid4(), "Stack 2"),
            StackId(uuid.uuid4(), "Stack 3"),
            StackId(uuid.uuid4(), "Stack Tomo"),
            StackId(uuid.uuid4(), "Stack Recon"),
        ]
        mwsd = ImageSaveDialog(None, stack_list, selected_stack_uuid=uuid.uuid4())

        # Existing behavior defaults to Recon/Tomo preference sorting.
        self.assertEqual(mwsd.stack_uuids[0], stack_list[4].id)
        self.assertEqual(mwsd.stackNames.currentIndex(), 0)
