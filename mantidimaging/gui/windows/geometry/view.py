# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from __future__ import annotations

from typing import TYPE_CHECKING

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.windows.geometry.presenter import GeometryWindowPresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover


class GeometryWindowView(BaseMainWindowView):

    def __init__(self, main_window: MainWindowView):
        super().__init__(None, 'gui/ui/geometry_window.ui')

        self.main_window = main_window
        self.presenter = GeometryWindowPresenter(self, main_window)
