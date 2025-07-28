# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from __future__ import annotations

from typing import TYPE_CHECKING

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.windows.geometry.presenter import GeometryWindowPresenter

## EXPERIMENTAL
import matplotlib

matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib import pyplot
from cil.utilities.display import show_geometry
## EXPERIMENTAL

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent, figure, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(figure)


class GeometryWindowView(BaseMainWindowView):

    def __init__(self, main_window: MainWindowView):
        super().__init__(None, 'gui/ui/geometry_window.ui')

        self.main_window = main_window
        self.presenter = GeometryWindowPresenter(self, main_window)

        test_uuid = None
        for u in self.main_window.stack_list:
            if u.id is not None:
                test_uuid = u.id
                break

        test_geometry = self.main_window.get_stack(test_uuid).geometry

        test_plot: Figure = show_geometry(test_geometry)

        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        sc = MplCanvas(self, figure=test_plot, width=5, height=4, dpi=100)
        sc.axes.plot([0, 1, 2, 3, 4], [10, 1, 20, 3, 40])
        self.setCentralWidget(sc)
