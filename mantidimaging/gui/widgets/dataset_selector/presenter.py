# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import traceback
from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING, List, Tuple, Union, Optional
from uuid import UUID

from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.utility import BlockQtSignals

if TYPE_CHECKING:
    from mantidimaging.gui.widgets.dataset_selector.view import DatasetSelectorWidgetView


class Notification(Enum):
    RELOAD_DATASETS = 0
    SELECT_ELIGIBLE_STACK = 1


class DatasetSelectorWidgetPresenter(BasePresenter):
    view: 'DatasetSelectorWidgetView'
    show_stacks: bool

    def __init__(self,
                 view: 'DatasetSelectorWidgetView',
                 show_stacks: bool = False,
                 relevant_dataset_types: Union[type, Tuple[type]] = None):
        super().__init__(view)

        self.current_dataset: Optional['UUID'] = None
        self.show_stacks = show_stacks
        self.relevant_dataset_types = relevant_dataset_types

    def notify(self, signal: Notification) -> None:
        try:
            if signal == Notification.RELOAD_DATASETS:
                self.do_reload_datasets()
            elif signal == Notification.SELECT_ELIGIBLE_STACK:
                self.do_select_eligible_stack()

        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    def do_reload_datasets(self) -> None:
        old_selection = self.view.currentText()
        # Don't want signals emitted when changing the list of stacks
        with BlockQtSignals([self.view]):
            # Clear the previous entries from the drop down menu
            self.view.clear()

            # Get all the new stacks
            dataset_list = self._get_dataset_list()
            user_friendly_names = [item[1] for item in dataset_list]

            for uuid, name in dataset_list:
                self.view.addItem(name, uuid)

            # If the previously selected window still exists with the same name,
            # reselect it, otherwise default to the first item
            if old_selection in user_friendly_names:
                new_selected_index = user_friendly_names.index(old_selection)
            else:
                new_selected_index = 0

            self.view.setCurrentIndex(new_selected_index)

        self.view.datasets_updated.emit()
        self.handle_selection(new_selected_index)

    def _get_dataset_list(self) -> List[Tuple[UUID, str]]:
        result = []
        for dataset in self.view.main_window.presenter.datasets:
            # If no relevant dataset types have been specified then all should be included
            if not self.relevant_dataset_types or isinstance(dataset, self.relevant_dataset_types):
                if not self.show_stacks:
                    result.append((dataset.id, dataset.name))
                else:
                    for stack in dataset.all:
                        result.append((stack.id, stack.name))

        return result

    def handle_selection(self, index: int) -> None:
        self.current_dataset = self.view.itemData(index)
        if self.show_stacks:
            self.view.stack_selected_uuid.emit(self.current_dataset)
        else:
            self.view.dataset_selected_uuid.emit(self.current_dataset)

    def do_select_eligible_stack(self) -> None:
        for i in range(self.view.count()):
            name = self.view.itemText(i).lower()
            if "dark" not in name and "flat" not in name and "180deg" not in name:
                self.view.setCurrentIndex(i)
                break

    @property
    def current_is_strict(self) -> bool:
        return self.view.main_window.is_dataset_strict(self.current_dataset)
