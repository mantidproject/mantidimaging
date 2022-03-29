# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

from mantidimaging.gui.windows.main.nexus_save_dialog import NexusSaveDialog
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class NexusSaveDialogTest(unittest.TestCase):
    def test_save_calls_execute_nexus_save(self):
        parent = mock.Mock()
        nexus_save_dialog = NexusSaveDialog(None, [])
        nexus_save_dialog.parent = mock.Mock(return_value=parent)

        dataset_id = "dataset-id"
        nexus_save_dialog.dataset_uuids = [dataset_id]
        nexus_save_dialog.datasetNames.currentIndex = mock.Mock(return_value=0)

        nexus_save_dialog.save()
        parent.execute_nexus_save.assert_called_once()
