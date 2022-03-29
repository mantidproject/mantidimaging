# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

from mantidimaging.gui.windows.main.nexus_save_dialog import NexusSaveDialog
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class NexusSaveDialogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nexus_save_dialog = NexusSaveDialog(None, [])

    def test_save_calls_execute_nexus_save(self):
        parent = mock.Mock()
        self.nexus_save_dialog.parent = mock.Mock(return_value=parent)

        dataset_id = "dataset-id"
        self.nexus_save_dialog.dataset_uuids = [dataset_id]
        self.nexus_save_dialog.datasetNames.currentIndex = mock.Mock(return_value=0)

        self.nexus_save_dialog.save()
        parent.execute_nexus_save.assert_called_once()

    def test_save_path(self):
        save_path = "a/save/path"
        self.nexus_save_dialog.savePath.text = mock.Mock(return_value=save_path)
        self.assertEqual(save_path, self.nexus_save_dialog.save_path())
