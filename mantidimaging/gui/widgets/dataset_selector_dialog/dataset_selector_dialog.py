# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING, Optional

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton

from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.gui.widgets.dataset_selector.view import DatasetSelectorWidgetView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main.view import MainWindowView  # pragma: no cover


class DatasetSelectorDialog(QDialog):
    def __init__(self, main_window: Optional['MainWindowView'], title: Optional[str] = None):
        super().__init__(main_window)

        self.selected_dataset = None

        self.setModal(True)
        self.setMinimumWidth(300)

        if title is not None:
            self.setWindowTitle(title)

        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.addWidget(QLabel("What dataset is the 180 projection being loaded for?", self))

        # Dataset selector
        self.dataset_selector_widget = DatasetSelectorWidgetView(self, relevant_dataset_types=StrictDataset)
        self.dataset_selector_widget.subscribe_to_main_window(main_window)  # type: ignore
        self.vertical_layout.addWidget(self.dataset_selector_widget)

        # Button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        self.ok_button = QPushButton("Select")
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.button_layout.addWidget(self.ok_button)
        self.vertical_layout.addLayout(self.button_layout)

    def on_ok_clicked(self):
        self.selected_dataset = self.dataset_selector_widget.current()
        self.done(QDialog.DialogCode.Accepted)
