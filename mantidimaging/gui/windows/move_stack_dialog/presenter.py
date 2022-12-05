# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
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
            self.view.show_error_dialog(str(err))

    def _on_accepted(self):
        """
        Calls the execute move stack method in the main view.
        """
        self.view.parent_view.execute_move_stack(self.view.origin_dataset_id, self.view.stack_id,
                                                 self.view.destination_stack_type, self.view.destination_dataset_name)
