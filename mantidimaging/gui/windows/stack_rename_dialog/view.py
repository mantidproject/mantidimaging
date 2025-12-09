# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from math import degrees
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QLabel, QGridLayout, QLineEdit, QDialogButtonBox

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.stack_rename_dialog.presenter import Notification
from mantidimaging.gui.windows.stack_rename_dialog.presenter import StackRenamePresenter

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack
    from mantidimaging.core.data.dataset import Dataset


class StackRenameDialog(BaseDialogView):

    def __init__(self, parent, stack: ImageStack, origin_dataset: Dataset):
        super().__init__(parent)
        self.parent_view = parent
        self.origin_dataset = origin_dataset

        self.presenter = StackRenamePresenter(self)

        self.stack = stack

        self.setWindowTitle(f"Rename Stack: {origin_dataset.name}")

        QBtn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self.layout = QGridLayout()

        self.new_name_field = QLineEdit()

        self.layout.addWidget(QLabel("New Dataset Name: "), 1, 1)
        self.layout.addWidget(self.new_name_field, 1, 2)

        self.layout.addWidget(self.buttonBox, 2, 2)

        self.setLayout(self.layout)

    def accept(self) -> None:
        self.presenter.notify(Notification.ACCEPTED)
        self.close()
