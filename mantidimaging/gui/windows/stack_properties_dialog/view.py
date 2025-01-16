# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import uuid

from PyQt5.QtWidgets import QLabel, QGridLayout

from mantidimaging.core.data.dataset import Dataset

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.move_stack_dialog.presenter import Notification
from mantidimaging.gui.windows.stack_properties_dialog.presenter import StackPropertiesPresenter


class StackPropertiesDialog(BaseDialogView):

    def __init__(self, parent, stack_id: uuid.UUID, origin_dataset: Dataset, origin_data_type: str):
        super().__init__(parent)
        self.origin_dataset = origin_dataset

        self.presenter = StackPropertiesPresenter(self)

        self._stack_id = stack_id

        self.presenter.set_stack_from_data_type(origin_data_type)
        self.presenter.set_stack_data()
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
        self.layout.addWidget(QLabel(f"{self.stack_shape}"), 5, 2)

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
