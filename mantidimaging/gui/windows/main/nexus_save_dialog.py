# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import uuid
from typing import Optional, List

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFileDialog

from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.gui.utility import compile_ui

NXS_EXT = ".nxs"


class NexusSaveDialog(QDialog):

    selected_dataset = Optional[uuid.UUID]

    def __init__(self, parent, dataset_list: List[StrictDataset]):
        super().__init__(parent)
        compile_ui('gui/ui/nexus_save_dialog.ui', self)

        self.browseButton.clicked.connect(self._set_save_path)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Save).setEnabled(False)
        self.savePath.textChanged.connect(self.enable_save)
        self.sampleNameLineEdit.textChanged.connect(self.enable_save)

        self.dataset_uuids: List[uuid.UUID] = []
        self._create_dataset_lists(dataset_list)

        self.selected_dataset = None

    def _create_dataset_lists(self, dataset_list):
        if dataset_list:
            self.dataset_uuids, dataset_names = zip(*dataset_list)
            self.datasetNames.addItems(dataset_names)

    def accept(self) -> None:
        self.selected_dataset = self.dataset_uuids[self.datasetNames.currentIndex()]
        self.parent().execute_nexus_save()
        self.close()

    def save_path(self) -> str:
        """
        :return: The directory of the path as a Python string
        """
        return str(self.savePath.text())

    def sample_name(self) -> str:
        return str(self.sampleNameLineEdit.text())

    def enable_save(self):
        self.buttonBox.button(QDialogButtonBox.StandardButton.Save).setEnabled(self.save_path().strip() != ""
                                                                               and self.sample_name().strip() != "")

    def _set_save_path(self):
        path = QFileDialog.getSaveFileName(self, "Save NeXus file", "", f"NeXus (*{NXS_EXT})")[0]
        if os.path.splitext(path)[1] != NXS_EXT:
            path += NXS_EXT
        self.savePath.setText(path)
