# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import uuid

from PyQt5.QtWidgets import QComboBox, QFileDialog, QDialogButtonBox, QPushButton, QLineEdit, QLabel

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.add_images_to_dataset_dialog.presenter import AddImagesToDatasetPresenter, Notification


class AddImagesToDatasetDialog(BaseDialogView):
    imageTypeComboBox: QComboBox
    chooseFileButton: QPushButton
    filePathLineEdit: QLineEdit
    datasetNameText: QLabel

    def __init__(self, parent, dataset_id: uuid.UUID, strict_dataset: bool, dataset_name: str):
        super().__init__(parent, 'gui/ui/add_to_dataset.ui')

        self.parent_view = parent
        self.presenter = AddImagesToDatasetPresenter(self)
        self._dataset_id = dataset_id

        if strict_dataset:
            self.imageTypeComboBox.addItems(
                ["Sample", "Flat Before", "Flat After", "Dark Before", "Dark After", "Recon"])
        else:
            self.imageTypeComboBox.addItems(["Images", "Recon"])

        self.datasetNameText.setText(dataset_name)
        self.chooseFileButton.clicked.connect(self.choose_file_path)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        self.accepted.connect(self._on_accepted)

    def _on_accepted(self):
        self.presenter.notify(Notification.IMAGE_FILE_SELECTED)

    def choose_file_path(self):
        """
        Select a file in the stack path that we wish to add/replace in the dataset.
        """
        selected_file, _ = QFileDialog.getOpenFileName(caption="Images", filter="Image File (*.tif *.tiff)")
        if selected_file:
            self.filePathLineEdit.setText(selected_file)
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

    @property
    def path(self) -> str:
        """
        :return: The path string.
        """
        return self.filePathLineEdit.text()

    @property
    def images_type(self) -> str:
        """
        :return: The name of the image stack.
        """
        return self.imageTypeComboBox.currentText()

    @property
    def dataset_id(self) -> uuid.UUID:
        """
        :return: The ID of the parent dataset.
        """
        return self._dataset_id
