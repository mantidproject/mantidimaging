# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.widgets.dataset_selector.view import DatasetSelectorWidgetView
from PyQt5.QtWidgets import QGridLayout, QPushButton

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main.view import MainWindowView  # pragma: no cover


class MultipleStackSelect(BaseDialogView):

    def __init__(self, main_window: MainWindowView) -> None:
        super().__init__(main_window)

        layout = QGridLayout()
        self.setLayout(layout)

        self.stack_one = DatasetSelectorWidgetView(self, show_stacks=True)
        self.stack_one.subscribe_to_main_window(main_window)
        layout.addWidget(self.stack_one, 0, 1)

        self.stack_two = DatasetSelectorWidgetView(self, show_stacks=True)
        self.stack_two.subscribe_to_main_window(main_window)
        layout.addWidget(self.stack_two, 0, 2)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button, 1, 0, 1, 4)
