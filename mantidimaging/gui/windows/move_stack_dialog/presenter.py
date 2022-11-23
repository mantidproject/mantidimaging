# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import traceback
from enum import Enum, auto
from typing import TYPE_CHECKING

from mantidimaging.gui.mvp_base import BasePresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.move_stack_dialog.view import MoveStackDialog


class Notification(Enum):
    ACCEPTED = auto()


class MoveStackPresenter(BasePresenter):
    def __init__(self, view: 'MoveStackDialog'):
        super().__init__(view)

    def notify(self, n: Notification):
        try:
            if n == Notification.ACCEPTED:
                self._on_accepted()
        except RuntimeError as err:
            self.view.show_exception(str(err), traceback.format_exc())

    def _on_accepted(self):
        origin_dataset_id = self.view.origin_dataset_id
        stack_id = self.view.stack_id
        destination_data_type = self.view.destination_data_type
        destination_dataset_name = self.view.destination_dataset_name
        self.view.parent_view.presenter.execute_move_stack(origin_dataset_id, stack_id, destination_data_type,
                                                           destination_dataset_name)
