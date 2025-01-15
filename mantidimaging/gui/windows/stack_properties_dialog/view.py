# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QLabel, QGridLayout

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.move_stack_dialog.presenter import Notification
from mantidimaging.gui.windows.stack_properties_dialog.presenter import StackPropertiesPresenter

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack
    from mantidimaging.core.data.dataset import Dataset


class StackPropertiesDialog(BaseDialogView):

    stack: ImageStack

    def __init__(self, parent, stack: ImageStack, origin_dataset: Dataset, origin_data_type: str):
        super().__init__(parent)
        self.parent_view = parent
        self.origin_dataset = origin_dataset

        self.presenter = StackPropertiesPresenter(self)

        self.stack = stack

        self.presenter.set_stack_data()
        self.presenter.set_stack_directory()
        self.log_filename = self.presenter.get_log_filename()

        self.setWindowTitle(f"Stack Properties: {origin_dataset.name}")
        self.layout = QGridLayout()
        self.layout.addWidget(QLabel("Dataset Name: "), 1, 1)
        self.layout.addWidget(QLabel("File Path: "), 2, 1)
        self.layout.addWidget(QLabel("Data type: "), 3, 1)
        self.layout.addWidget(QLabel("Memory size: "), 4, 1)
        self.layout.addWidget(QLabel("Shape: "), 5, 1)
        self.layout.addWidget(QLabel("Log file: "), 6, 1)

        self.layout.addWidget(QLabel(f"{origin_dataset.name}"), 1, 2)
        self.layout.addWidget(QLabel(f"{self.directory}"), 2, 2)
        self.layout.addWidget(QLabel(f"{origin_data_type}"), 3, 2)
        self.layout.addWidget(QLabel(f"{round(self.stack_size_MB, 4)} MB"), 4, 2)
        self.layout.addWidget(QLabel(f"{self.stack_shape}"), 5, 2)
        self.layout.addWidget(QLabel(f"{self.log_filename}"), 6, 2)

        self.setLayout(self.layout)

    def accept(self) -> None:
        self.presenter.notify(Notification.ACCEPTED)
        self.close()
