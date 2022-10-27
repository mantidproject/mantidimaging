# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtWidgets import QComboBox, QFileDialog, QDialogButtonBox, QPushButton, QLineEdit

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.add_images_to_dataset_dialog.presenter import AddImagesToDatasetPresenter, Notification


class AddImagesToDatasetDialog(BaseDialogView):
    imageTypeComboBox: QComboBox
    chooseFileButton: QPushButton
    filePathLineEdit: QLineEdit

    def __init__(self, parent, strict_dataset: bool):
        super().__init__(parent, 'gui/ui/add_to_dataset.ui')

        self.parent_view = parent
        self.presenter = AddImagesToDatasetPresenter(self)

        self.imageTypeComboBox.setEnabled(strict_dataset)
        self.chooseFileButton.clicked.connect(self.choose_file_path)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        self.accepted.connect(self._on_accepted)

    def _on_accepted(self):
        self.presenter.notify(Notification.IMAGE_FILE_SELECTED)

    def choose_file_path(self):
        """
        Select the files to add/replace in the dataset.
        """
        selected_file, _ = QFileDialog.getOpenFileName(caption="Images", filter="Image File (*.tif *.tiff)")
        if selected_file:
            self.filePathLineEdit.setText(selected_file)
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

    @property
    def path(self):
        return self.filePathLineEdit.text()

    @property
    def images_type(self):
        return self.imageTypeComboBox.currentText()
