# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from enum import Enum, auto
from typing import TYPE_CHECKING

from mantidimaging.gui.mvp_base import BasePresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.move_stack_dialog.view import MoveStackDialog

STRICT_DATASET_ATTRS = ["Sample", "Flat Before", "Flat After", "Dark Before", "Dark After", "Recon"]
MIXED_DATASET_TYPES = ["Images", "Recon"]


class Notification(Enum):
    ACCEPTED = auto()
    DATASET_CHANGED = auto()


class MoveStackPresenter(BasePresenter):

    def __init__(self, view: MoveStackDialog):
        super().__init__(view)

    def notify(self, n: Notification):
        try:
            if n == Notification.ACCEPTED:
                self._on_accepted()
            if n == Notification.DATASET_CHANGED:
                self._on_dataset_changed()
        except RuntimeError as err:
            self.view.show_error_dialog(str(err))

    def _on_accepted(self):
        """
        Calls the execute move stack method in the main view.
        """
        self.view.parent_view.execute_move_stack(self.view.origin_dataset_id, self.view.stack_id,
                                                 self.view.destination_stack_type, self.view.destination_dataset_id)

    def _on_dataset_changed(self):
        """
        Change the contents of the destination type combo box when the destination dataset has changed.
        """
        self.view.destinationTypeComboBox.clear()

        if self.view.datasetSelector.current_is_strict():
            if self.view.datasetSelector.current() == self.view.origin_dataset_id:
                same_ds_list = STRICT_DATASET_ATTRS.copy()
                same_ds_list.remove(self.view.originDataType.text())
                self.view.destinationTypeComboBox.addItems(same_ds_list)
            else:
                self.view.destinationTypeComboBox.addItems(STRICT_DATASET_ATTRS)
        else:
            self.view.destinationTypeComboBox.addItems(MIXED_DATASET_TYPES)
