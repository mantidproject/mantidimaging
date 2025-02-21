# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mantidimaging.core.utility.size_calculator import full_size_MB
from mantidimaging.gui.mvp_base import BasePresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.stack_properties_dialog.view import StackPropertiesDialog


class StackPropertiesPresenter(BasePresenter):

    def __init__(self, view: StackPropertiesDialog):
        super().__init__(view)

    def set_stack_data(self) -> None:
        if self.view.stack is not None:
            self.view.stack_shape = self.view.stack.data.shape
        self.view.stack_size_MB = self.get_stack_size_MB()

    def set_stack_directory(self) -> None:
        if self.view.stack.filenames is not None:
            self.view.directory = Path(self.view.stack.filenames[0]).parent

    def get_stack_size_MB(self) -> float:
        return full_size_MB(self.view.stack.data.shape, self.view.stack.data.dtype)

    def get_log_filename(self) -> str:
        if 'log_file' in self.view.stack.metadata:
            return self.view.stack.metadata['log_file']
        else:
            return "N/A"
