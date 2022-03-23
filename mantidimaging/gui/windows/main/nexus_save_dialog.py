# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from typing import Optional, List

from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.gui.utility import select_directory, compile_ui


class NexusSaveDialog(QDialog):

    selected_dataset = Optional[uuid.UUID]

    def __init__(self, parent, dataset_list: List[StrictDataset]):
        super().__init__(parent)
        compile_ui('gui/ui/nexus_save_dialog.ui', self)

        self.browseButton.clicked.connect(lambda: select_directory(self.savePath, "Browse"))
        self.buttonBox.button(QDialogButtonBox.StandardButton.Save).clicked.connect(self.save)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Save).setEnabled(False)
        self.savePath.textChanged.connect(self.enable_save)

        if dataset_list:
            self.dataset_uuids, dataset_names = zip(*dataset_list)
            self.datasetNames.addItems(dataset_names)

        self.selected_dataset = None

    def save(self):
        self.selected_dataset = self.dataset_uuids[self.datasetNames.currentIndex()]
        self.parent().execute_nexus_save()

    def save_path(self) -> str:
        """
        :return: The directory of the path as a Python string
        """
        return str(self.savePath.text())

    def overwrite(self) -> bool:
        return self.overwriteAll.isChecked()

    def enable_save(self):
        self.buttonBox.button(QDialogButtonBox.StandardButton.Save).setEnabled(self.save_path() != "")
