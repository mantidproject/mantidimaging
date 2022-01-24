# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import traceback
from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING, List, Tuple
from uuid import UUID

from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.utility import BlockQtSignals

if TYPE_CHECKING:
    from mantidimaging.gui.widgets.dataset_selector.view import DatasetSelectorWidgetView


class Notification(Enum):
    RELOAD_DATASETS = 0


class DatasetSelectorWidgetPresenter(BasePresenter):
    view: 'DatasetSelectorWidgetView'

    def __init__(self, view):
        super().__init__(view)

        self.dataset_uuids = []
        self.current_dataset = None

    def notify(self, signal):
        try:
            if signal == Notification.RELOAD_DATASETS:
                self.do_reload_datasets()

        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    def do_reload_datasets(self):
        old_selection = self.view.currentText()
        # Don't want signals emitted when changing the list of stacks
        with BlockQtSignals([self.view]):
            # Clear the previous entries from the drop down menu
            self.view.clear()

            # Get all the new stacks
            dataset_list: List[Tuple[UUID, str]] = self.view.main_window.dataset_list
            self.dataset_uuids, user_friendly_names = \
                zip(*dataset_list) if dataset_list else (None, [])
            self.view.addItems(user_friendly_names)

            # If the previously selected window still exists with the same name,
            # reselect it, otherwise default to the first item
            if old_selection in user_friendly_names:
                new_selected_index = user_friendly_names.index(old_selection)
            else:
                new_selected_index = 0

            self.view.setCurrentIndex(new_selected_index)

        self.view.datasets_updated.emit()
        self.handle_selection(new_selected_index)

    def handle_selection(self, index):
        uuid = self.dataset_uuids[index] if self.dataset_uuids else None
        self.current_dataset = uuid
        self.view.dataset_selected_uuid.emit(uuid)
