# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from __future__ import annotations

from typing import TYPE_CHECKING

from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.geometry.model import GeometryWindowModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.geometry.view import GeometryWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main import MainWindowView


class GeometryWindowPresenter(BasePresenter):
    view: GeometryWindowView

    def __init__(self, view: GeometryWindowView, main_window: MainWindowView):
        super().__init__(view)
        self.view = view
        self.model = GeometryWindowModel()
        self.main_window = main_window
