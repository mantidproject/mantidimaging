# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from enum import Enum, auto
from logging import getLogger


from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.stack_properties_dialog.view import StackPropertiesDialog
logger = getLogger(__name__)


class Notification(Enum):
    ACCEPTED = auto()


class StackRenamePresenter(BasePresenter):

    def __init__(self, view: StackPropertiesDialog):
        super().__init__(view)

    def notify(self, n: Notification) -> None:
        try:
            if n == Notification.ACCEPTED:
                self._on_accepted()
        except RuntimeError as err:
            self.view.show_error_dialog(str(err))

    def _on_accepted(self) -> None:
        """
        Calls the execute rename dataset method in the main view.
        """
        assert self.view.new_name_field.text(), "Stack name can not be empty."
        self.view.parent_view.execute_rename_dataset(self.view.stack, self.view.new_name_field.text())
