# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import uuid

from PyQt5.QtWidgets import QLabel, QComboBox, QGridLayout

from mantidimaging.core.data.dataset import Dataset

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.move_stack_dialog.presenter import Notification


class StackPropertiesDialog(BaseDialogView):

    originDatasetName: QLabel
    originDataType: QLabel

    destinationTypeComboBox: QComboBox

    def __init__(self, parent, origin_dataset_id: uuid.UUID, stack_id: uuid.UUID, origin_dataset: Dataset,
                 origin_data_type: str):
        super().__init__(parent)

        self._stack_id = stack_id

        if origin_data_type == "Sample":
            self.stack = origin_dataset.sample
        elif origin_data_type == "Flat Before":
            self.stack = origin_dataset.flat_before
        elif origin_data_type == "Flat After":
            self.stack = origin_dataset.flat_after
        elif origin_data_type == "Dark Before":
            self.stack = origin_dataset.dark_before
        elif origin_data_type == "Dark After":
            self.stack = origin_dataset.dark_after

        if self.stack is not None:
            if self.stack.filenames is not None:
                self.directory = self.stack.filenames[0].replace(self.stack.filenames[0].split("\\")[-1], '')
            stack_shape = self.stack.data.shape
        self.stack_size_MB = sum(
            os.path.getsize(self.directory + f)
            for f in os.listdir(self.directory) if os.path.isfile(self.directory + f)) / 1024 / 1024

        self.parent_view = parent

        self.setWindowTitle(f"Stack Properties: {origin_dataset.name}")
        self.layout = QGridLayout()
        self.layout.addWidget(QLabel("Dataset Name: "), 1, 1)
        self.layout.addWidget(QLabel("File Path: "), 2, 1)
        self.layout.addWidget(QLabel("Data type: "), 3, 1)
        self.layout.addWidget(QLabel("Memory size: "), 4, 1)
        self.layout.addWidget(QLabel("Shape: "), 5, 1)

        self.layout.addWidget(QLabel(f"{origin_dataset.name}"), 1, 2)
        self.layout.addWidget(QLabel(f"{self.directory}"), 2, 2)
        self.layout.addWidget(QLabel(f"{origin_data_type}"), 3, 2)
        self.layout.addWidget(QLabel(f"{round(self.stack_size_MB, 4)} MB"), 4, 2)
        self.layout.addWidget(QLabel(f"{stack_shape}"), 5, 2)

        self.setLayout(self.layout)

    def accept(self) -> None:
        self.presenter.notify(Notification.ACCEPTED)
        self.close()

    @property
    def origin_dataset_id(self) -> uuid.UUID:
        return self._origin_dataset_id

    @property
    def stack_id(self) -> uuid.UUID:
        return self._stack_id
