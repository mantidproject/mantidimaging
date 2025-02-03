# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

from mantidimaging.core.utility.size_calculator import full_size_MB
from mantidimaging.gui.mvp_base import BasePresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.stack_properties_dialog.view import StackPropertiesDialog


class StackPropertiesPresenter(BasePresenter):

    def __init__(self, view: StackPropertiesDialog):
        super().__init__(view)

    def set_stack_from_data_type(self, origin_data_type) -> None:
        if origin_data_type == "Sample":
            self.view.stack = self.view.origin_dataset.sample
        elif origin_data_type == "Flat Before":
            self.view.stack = self.view.origin_dataset.flat_before
        elif origin_data_type == "Flat After":
            self.view.stack = self.view.origin_dataset.flat_after
        elif origin_data_type == "Dark Before":
            self.view.stack = self.view.origin_dataset.dark_before
        elif origin_data_type == "Dark After":
            self.view.stack = self.view.origin_dataset.dark_after

    def set_stack_data(self):
        if self.view.stack is not None:
            if self.view.stack.filenames is not None:
                self.view.directory = self.view.stack.filenames[0].replace(self.view.stack.filenames[0].split("\\")[-1],
                                                                           '')
            self.view.stack_shape = self.view.stack.data.shape
        self.view.stack_size_MB = self.get_stack_size_MB()

    def get_stack_size_MB(self):
        return full_size_MB(self.view.stack.data.shape, self.view.stack.data.dtype)
