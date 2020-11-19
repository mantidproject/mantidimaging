# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import Optional

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QSpacerItem, QPushButton
from mantidimaging.gui.widgets.stack_selector import StackSelectorWidgetView


class StackSelectorDialog(QDialog):
    def __init__(self, main_window, title: Optional[str] = None, message: Optional[str] = None):
        super().__init__(main_window)

        self.selected_stack = None

        self.setModal(True)
        self.setMinimumWidth(300)

        if title is not None:
            self.setWindowTitle(title)

        self.vertical_layout = QVBoxLayout(self)

        if message is None:
            self.message_label = QLabel("Select the stack", self)
        else:
            self.message_label = QLabel(message, self)

        self.vertical_layout.addWidget(self.message_label)

        # Stack selector
        self.stack_selector_widget = StackSelectorWidgetView(self)
        self.stack_selector_widget.subscribe_to_main_window(main_window)
        self._select_tomo()
        self.vertical_layout.addWidget(self.stack_selector_widget)

        # Button layout
        self.button_layout = QHBoxLayout(self)
        self.button_layout.addStretch()
        self.ok_button = QPushButton("Select")
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.button_layout.addWidget(self.ok_button)
        self.vertical_layout.addLayout(self.button_layout)

        self.setLayout(self.vertical_layout)

    def _select_tomo(self):
        for index in range(0, self.stack_selector_widget.count()):
            item_string = self.stack_selector_widget.itemText(index).lower()
            if "tomo" in item_string:
                self.stack_selector_widget.setCurrentIndex(index)
                return

    def on_ok_clicked(self):
        self.selected_stack = self.stack_selector_widget.currentText()
        self.close()
