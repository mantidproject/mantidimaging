# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import os
import uuid
from collections.abc import Iterable

from PyQt5.QtWidgets import QDialogButtonBox, QFileDialog, QRadioButton

from mantidimaging.core.data.dataset import Dataset
from mantidimaging.gui.mvp_base import BaseDialogView

NXS_EXT = ".nxs"


class NexusSaveDialog(BaseDialogView):

    selected_dataset: uuid.UUID | None
    floatRadioButton: QRadioButton
    intRadioButton: QRadioButton

    def __init__(self, parent, dataset_list: Iterable[Dataset]):
        super().__init__(parent, 'gui/ui/nexus_save_dialog.ui')

        self.browseButton.clicked.connect(self._set_save_path)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Save).setEnabled(False)
        self.savePath.textChanged.connect(self.enable_save)
        self.savePath.editingFinished.connect(self._check_extension)
        self.sampleNameLineEdit.textChanged.connect(self.enable_save)

        self.dataset_uuids: list[uuid.UUID] = []
        self._create_dataset_lists(dataset_list)

        self.selected_dataset = None

    def _create_dataset_lists(self, dataset_list: Iterable[Dataset]):
        if dataset_list:
            self.dataset_uuids = [ds.id for ds in dataset_list]
            dataset_names = [ds.name for ds in dataset_list]
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

    def enable_save(self) -> None:
        self.buttonBox.button(QDialogButtonBox.StandardButton.Save).setEnabled(self.save_path().strip() != ""
                                                                               and self.sample_name().strip() != "")

    def _set_save_path(self) -> None:
        path = QFileDialog.getSaveFileName(self, "Save NeXus file", "", f"NeXus (*{NXS_EXT})")[0]
        self.savePath.setText(path)
        self._check_extension()

    def _check_extension(self) -> None:
        path = self.save_path()
        if os.path.splitext(path)[1] != NXS_EXT:
            self.savePath.setText(path + NXS_EXT)

    @property
    def save_as_float(self) -> bool:
        return self.floatRadioButton.isChecked()
