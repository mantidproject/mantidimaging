# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING
from mantidimaging.gui.widgets.stack_selector.view import StackSelectorWidgetView
from PyQt5.QtWidgets import QDialog, QGridLayout, QPushButton

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main.view import MainWindowView  # pragma: no cover


class MultipleStackSelect(QDialog):
    def __init__(self, main_window: 'MainWindowView') -> None:
        super().__init__(main_window)

        layout = QGridLayout()
        self.setLayout(layout)

        self.stack_one = StackSelectorWidgetView(self)
        self.stack_one.subscribe_to_main_window(main_window)
        layout.addWidget(self.stack_one, 0, 1)

        self.stack_two = StackSelectorWidgetView(self)
        self.stack_two.subscribe_to_main_window(main_window)
        layout.addWidget(self.stack_two, 0, 2)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button, 1, 0, 1, 4)
