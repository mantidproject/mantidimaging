# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal
from pyqtgraph import GraphicsLayoutWidget, PlotItem, LinearRegionItem, ROI

from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView
from mantidimaging.core.utility.sensible_roi import SensibleROI

if TYPE_CHECKING:
    from .view import SpectrumViewerWindowView


class SpectrumWidget(GraphicsLayoutWidget):
    image: MIMiniImageView
    spectrum: PlotItem
    range_control: LinearRegionItem
    roi: ROI

    range_changed = pyqtSignal()

    def __init__(self, parent: 'SpectrumViewerWindowView'):
        super().__init__(parent)
        self.parent = parent

        self.image = MIMiniImageView(name="Projection", parent=parent)
        self.addItem(self.image, 0, 0)

        self.nextRow()
        self.spectrum = self.addPlot()

        self.ci.layout.setRowStretchFactor(0, 3)
        self.ci.layout.setRowStretchFactor(1, 1)

        self.range_control = LinearRegionItem()
        self.range_control.sigRegionChanged.connect(self.range_changed.emit)

        self.roi = ROI(pos=(0, 0))

    def add_range(self, range_min: int, range_max: int):
        self.range_control.setBounds((range_min, range_max))
        self.range_control.setRegion((range_min, range_max))
        self.spectrum.addItem(self.range_control)

    def get_tof_range(self) -> tuple[int, int]:
        r_min, r_max = self.range_control.getRegion()
        return int(r_min), int(r_max)

    def add_roi(self, roi: SensibleROI):
        self.roi.setPos((roi.left, roi.top))
        self.roi.setSize((roi.width, roi.height))
        self.roi.addScaleHandle([1, 1], [0, 0])
        self.roi.addScaleHandle([1, 0], [0, 1])
        self.roi.addScaleHandle([0, 0], [1, 1])
        self.roi.addScaleHandle([0, 1], [1, 0])
        self.image.vb.addItem(self.roi)
