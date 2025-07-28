# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from __future__ import annotations

from typing import TYPE_CHECKING

import io

from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap

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

    test_qlabel: QLabel

    def __init__(self, main_window: MainWindowView):
        super().__init__(None, 'gui/ui/geometry_window.ui')

        self.main_window = main_window
        self.presenter = GeometryWindowPresenter(self, main_window)

        test_geometry = None
        for u in self.main_window.stack_list:
            if u.id is not None and self.main_window.get_stack(u.id).geometry is not None:
                test_geometry = self.main_window.get_stack(u.id).geometry
                break

        test_plot: Figure = show_geometry(test_geometry).figure

        # Render to an in-memory buffer
        buf = io.BytesIO()
        test_plot.savefig(buf, format="png")
        buf.seek(0)

        # Load PNG data into QPixmap
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())

        # Create a QLabel and set its pixmap
        self.test_qlabel.setPixmap(pixmap)
