# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.core.data.imagestack import StackNotFoundError

import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .view import MI3DViewerWindowView
    from mantidimaging.gui.windows.main import MainWindowView


class MI3DViewerPresenter(BasePresenter):
    view: MI3DViewerWindowView

    def __init__(self, view: MI3DViewerWindowView, main_window: MainWindowView):
        self.view = view
        self.main_window = main_window

    def handle_stack_change(self) -> None:
        current_stack_uuid = self.view.current_stack
        current_stack = self.main_window.get_stack(current_stack_uuid)
        if current_stack is None:
            raise StackNotFoundError("No ImageStack found for UUID")
        array3d: np.ndarray = current_stack.data
        self.view._update_viewer(array3d)
