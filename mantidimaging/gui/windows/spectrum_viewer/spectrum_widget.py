# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING

from pyqtgraph import GraphicsLayoutWidget, PlotItem

from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView

if TYPE_CHECKING:
    from .view import SpectrumViewerWindowView


class SpectrumWidget(GraphicsLayoutWidget):
    image: MIMiniImageView
    spectrum: PlotItem

    def __init__(self, parent: 'SpectrumViewerWindowView'):
        super().__init__(parent)
        self.parent = parent

        self.image = MIMiniImageView(name="Projection", parent=parent)
        self.addItem(self.image, 0, 0)

        self.nextRow()
        self.spectrum = self.addPlot()

        self.ci.layout.setRowStretchFactor(0, 3)
        self.ci.layout.setRowStretchFactor(1, 1)
