# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox

from .presenter import (StackSelectorWidgetPresenter, Notification)

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # pragma: no cover


def _string_contains_all_parts(string: str, parts: list) -> bool:
    for part in parts:
        if part.lower() not in string:
            return False
    return True


class StackSelectorWidgetView(QComboBox):
    stacks_updated = pyqtSignal()

    stack_selected_uuid = pyqtSignal('PyQt_PyObject')

    main_window: 'MainWindowView'

    def __init__(self, parent):
        super().__init__(parent)

        self.presenter = StackSelectorWidgetPresenter(self)

        self.currentIndexChanged[int].connect(self.presenter.handle_selection)

    def subscribe_to_main_window(self, main_window: 'MainWindowView'):
        self.main_window = main_window

        # Initial population of stack list
        self.presenter.notify(Notification.RELOAD_STACKS)

        # Connect signal for auto update on stack change
        self.main_window.model_changed.connect(self._handle_loaded_stacks_changed)

    def unsubscribe_from_main_window(self):
        """
        Removes connections to main window.

        Must be called before the widget is destroyed.
        """
        if self.main_window:
            # Disconnect signal
            self.main_window.model_changed.disconnect(self._handle_loaded_stacks_changed)

    def _handle_loaded_stacks_changed(self):
        """
        Handle a change in loaded stacks.
        """
        self.presenter.notify(Notification.RELOAD_STACKS)

    def current(self):
        return self.presenter.current_stack

    def select_eligible_stack(self):
        self.presenter.notify(Notification.SELECT_ELIGIBLE_STACK)

    def try_to_select_relevant_stack(self, name: str) -> None:
        # Split based on whitespace
        name_parts = name.split()
        for i in range(self.count()):
            # If widget text contains all name parts
            if _string_contains_all_parts(self.itemText(i).lower(), name_parts):
                self.setCurrentIndex(i)
                break
