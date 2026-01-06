# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QLabel, QGridLayout, QLineEdit, QDialogButtonBox

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.stack_rename_dialog.presenter import Notification
from mantidimaging.gui.windows.stack_rename_dialog.presenter import StackRenamePresenter

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack
    from mantidimaging.core.data.dataset import Dataset


class StackRenameDialog(BaseDialogView):

    def __init__(self, parent, stack: Dataset | ImageStack):
        super().__init__(parent)
        self.parent_view = parent

        self.presenter = StackRenamePresenter(self)

        self.stack = stack
        self.stack_id = stack.id
        self.stack_name = stack.name

        self.setWindowTitle(f"Rename Stack/Dataset: {self.stack.name}")

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)

        self.buttonBox.rejected.connect(self.close)

        self.layout = QGridLayout()

        self.new_name_field = QLineEdit()

        self.layout.addWidget(QLabel("New Stack/Dataset Name: "), 1, 1)
        self.layout.addWidget(self.new_name_field, 1, 2)

        self.layout.addWidget(self.buttonBox, 2, 2)

        self.setLayout(self.layout)

    def accept(self) -> None:
        self.presenter.notify(Notification.ACCEPTED)
        self.close()
