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
                pass
        except RuntimeError as err:
            self.view.show_exception(str(err), traceback.format_exc())
