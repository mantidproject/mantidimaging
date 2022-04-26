# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

from mantidimaging.gui.windows.main.nexus_save_dialog import NexusSaveDialog
from mantidimaging.gui.windows.main.presenter import DatasetId
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class NexusSaveDialogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nexus_save_dialog = NexusSaveDialog(None, [])

    def test_accept_calls_execute_nexus_save(self):
        parent = mock.Mock()
        self.nexus_save_dialog.parent = mock.Mock(return_value=parent)

        self.nexus_save_dialog.dataset_uuids = ["dataset-id"]
        self.nexus_save_dialog.datasetNames.currentIndex = mock.Mock(return_value=0)

        self.nexus_save_dialog.accept()
        parent.execute_nexus_save.assert_called_once()

    def test_save_path(self):
        save_path = "a/save/path"
        self.nexus_save_dialog.savePath.text = mock.Mock(return_value=save_path)
        self.assertEqual(save_path, self.nexus_save_dialog.save_path())

    def test_sample_name(self):
        sample_name = "sample-name"
        self.nexus_save_dialog.sampleNameLineEdit.text = mock.Mock(return_value=sample_name)
        self.assertEqual(sample_name, self.nexus_save_dialog.sample_name())

    def test_save_disabled_when_no_save_path(self):
        self.nexus_save_dialog.savePath.text = mock.Mock(return_value="")
        self.nexus_save_dialog.sampleNameLineEdit.text = mock.Mock(return_value="sample-name")
        self.nexus_save_dialog.buttonBox = mock.Mock()

        self.nexus_save_dialog.enable_save()
        self.nexus_save_dialog.buttonBox.button.return_value.setEnabled.assert_called_once_with(False)

    def test_save_disabled_when_no_sample_name(self):
        self.nexus_save_dialog.savePath.text = mock.Mock(return_value="save-path")
        self.nexus_save_dialog.sampleNameLineEdit.text = mock.Mock(return_value="")
        self.nexus_save_dialog.buttonBox = mock.Mock()

        self.nexus_save_dialog.enable_save()
        self.nexus_save_dialog.buttonBox.button.return_value.setEnabled.assert_called_once_with(False)

    def test_save_enabled(self):
        self.nexus_save_dialog.savePath.text = mock.Mock(return_value="save-path")
        self.nexus_save_dialog.sampleNameLineEdit.text = mock.Mock(return_value="sample-name")
        self.nexus_save_dialog.buttonBox = mock.Mock()

        self.nexus_save_dialog.enable_save()
        self.nexus_save_dialog.buttonBox.button.return_value.setEnabled.assert_called_once_with(True)

    def test_dataset_lists_creation(self):
        dataset_id = "dataset-id"
        dataset_name = "dataset-name"
        self.nexus_save_dialog.datasetNames = mock.Mock()
        self.nexus_save_dialog._create_dataset_lists([DatasetId(dataset_id, dataset_name)])

        self.assertEqual(self.nexus_save_dialog.dataset_uuids, (dataset_id, ))
        self.nexus_save_dialog.datasetNames.addItems.assert_called_once_with((dataset_name, ))

    @mock.patch("mantidimaging.gui.windows.main.nexus_save_dialog.QFileDialog.getSaveFileName")
    def test_set_save_path_adds_extension(self, get_save_file_name_mock):
        save_path = "save_path"
        get_save_file_name_mock.return_value = (save_path, )
        self.nexus_save_dialog._set_save_path()
        self.assertEqual(save_path + ".nxs", self.nexus_save_dialog.savePath.text())

    @mock.patch("mantidimaging.gui.windows.main.nexus_save_dialog.QFileDialog.getSaveFileName")
    def test_set_save_path_doesnt_add_extention_when_not_needed(self, get_save_file_name_mock):
        save_path = "save_path.nxs"
        get_save_file_name_mock.return_value = (save_path, )
        self.nexus_save_dialog._set_save_path()
        self.assertEqual(save_path, self.nexus_save_dialog.savePath.text())
