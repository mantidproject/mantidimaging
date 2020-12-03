# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from enum import Enum, auto
from typing import TYPE_CHECKING, Tuple

from mantidimaging.core.utility.savu_interop.plugin_list import SAVUPluginListEntry

from .model import ProcessListModel

if TYPE_CHECKING:
    from .view import ProcessListView  # pragma: no cover


class Notification(Enum):
    CHANGE_ORDER = auto()
    REMOVE_PLUGIN = auto()


class ProcessListPresenter:
    def __init__(self, view: 'ProcessListView'):
        self.view = view
        self.model: ProcessListModel = ProcessListModel()

    def notify(self, signal: Notification):
        if signal == Notification.CHANGE_ORDER:
            if self.view.order_change_request is None:
                raise RuntimeError("Process list view 'order_change_request' was unexpectedly unset")
            self.change_order(self.view.order_change_request)
            self.view.order_change_request = None

        elif signal == Notification.REMOVE_PLUGIN:
            if self.view.to_remove is None:
                raise RuntimeError("Process list view 'to_remove' was unexpectedly unset")
            self.remove_plugin(self.view.to_remove)
            self.view.to_remove = None

    def add_plugin(self, plugin: SAVUPluginListEntry):
        self.view.display_plugin(plugin.name.decode("utf-8"))
        self.model.plugins.append(plugin)

    def change_order(self, indices_to_change: Tuple[int, int]):
        start_index, new_index = indices_to_change
        self.view.swap(start_index, new_index)
        self.model.plugins[start_index], self.model.plugins[new_index] = \
            self.model.plugins[new_index], self.model.plugins[start_index]

    def remove_plugin(self, index: int):
        self.view.remove_plugin(index)
        self.model.plugins.pop(index)

    def overwrite_plugin(self, index: int, entry: SAVUPluginListEntry):
        self.model.plugins[index] = entry
