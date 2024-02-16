# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional, Union, Tuple, List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox

from mantidimaging.gui.widgets.dataset_selector.presenter import DatasetSelectorWidgetPresenter, Notification

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView


def _string_contains_all_parts(string: str, parts: List[str]) -> bool:
    for part in parts:
        if part.lower() not in string:
            return False
    return True


class DatasetSelectorWidgetView(QComboBox):
    datasets_updated = pyqtSignal()
    dataset_selected_uuid = pyqtSignal('PyQt_PyObject')
    stack_selected_uuid = pyqtSignal('PyQt_PyObject')

    main_window: 'MainWindowView'

    def __init__(self,
                 parent,
                 show_stacks: bool = False,
                 relevant_dataset_types: Union[type, Tuple[type]] | None = None):
        super().__init__(parent)

        self.presenter = DatasetSelectorWidgetPresenter(self,
                                                        show_stacks=show_stacks,
                                                        relevant_dataset_types=relevant_dataset_types)
        self.currentIndexChanged[int].connect(self.presenter.handle_selection)

    def subscribe_to_main_window(self, main_window: 'MainWindowView') -> None:
        self.main_window = main_window

        # Initial population of dataset list
        self.presenter.notify(Notification.RELOAD_DATASETS)

        # Connect signal for auto update on stack change
        self.main_window.model_changed.connect(self._handle_loaded_datasets_changed)

    def unsubscribe_from_main_window(self) -> None:
        """
        Removes connections to main window.

        Must be called before the widget is destroyed.
        """
        if self.main_window:
            # Disconnect signal
            self.main_window.model_changed.disconnect(self._handle_loaded_datasets_changed)

    def _handle_loaded_datasets_changed(self) -> None:
        """
        Handle a change in loaded stacks.
        """
        self.presenter.notify(Notification.RELOAD_DATASETS)

    def current(self) -> Optional[uuid.UUID]:
        return self.presenter.current_dataset

    def try_to_select_relevant_stack(self, name: str) -> None:
        # Split based on whitespace
        name_parts = name.split()
        for i in range(self.count()):
            # If widget text contains all name parts
            if _string_contains_all_parts(self.itemText(i).lower(), name_parts):
                self.setCurrentIndex(i)
                break

    def select_eligible_stack(self) -> None:
        self.presenter.notify(Notification.SELECT_ELIGIBLE_STACK)

    def current_is_strict(self) -> bool:
        return self.presenter.current_is_strict
