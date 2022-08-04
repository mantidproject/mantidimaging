# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal
from pyqtgraph import GraphicsLayoutWidget, PlotItem, LinearRegionItem, ROI

from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint

if TYPE_CHECKING:
    from .view import SpectrumViewerWindowView


class SpectrumWidget(GraphicsLayoutWidget):
    image: MIMiniImageView
    spectrum: PlotItem
    range_control: LinearRegionItem
    roi: ROI

    range_changed = pyqtSignal(object)
    roi_changed = pyqtSignal()

    def __init__(self, parent: 'SpectrumViewerWindowView'):
        super().__init__(parent)
        self.parent = parent

        self.image = MIMiniImageView(name="Projection", parent=parent)
        self.addItem(self.image, 0, 0)

        self.nextRow()
        self.spectrum = self.addPlot()

        self.nextRow()
        self._tof_range_label = self.addLabel()

        self.ci.layout.setRowStretchFactor(0, 3)
        self.ci.layout.setRowStretchFactor(1, 1)

        self.range_control = LinearRegionItem()
        self.range_control.sigRegionChanged.connect(self._handle_tof_range_changed)

        self.roi = ROI(pos=(0, 0), rotatable=False, scaleSnap=True, translateSnap=True)
        self.roi.sigRegionChanged.connect(self.roi_changed.emit)

    def add_range(self, range_min: int, range_max: int):
        self.range_control.setBounds((range_min, range_max))
        self.range_control.setRegion((range_min, range_max))
        self.spectrum.addItem(self.range_control)
        self._set_tof_range_label(range_min, range_max)

    def get_tof_range(self) -> tuple[int, int]:
        r_min, r_max = self.range_control.getRegion()
        return int(r_min), int(r_max)

    def add_roi(self, roi: SensibleROI):
        self.roi.setPos((roi.left, roi.top))
        self.roi.setSize((roi.width, roi.height))
        self.roi.maxBounds = self.roi.parentBounds()
        self.roi.addScaleHandle([1, 1], [0, 0])
        self.roi.addScaleHandle([1, 0], [0, 1])
        self.roi.addScaleHandle([0, 0], [1, 1])
        self.roi.addScaleHandle([0, 1], [1, 0])
        self.image.vb.addItem(self.roi)

    def get_roi(self) -> SensibleROI:
        pos = CloseEnoughPoint(self.roi.pos())
        size = CloseEnoughPoint(self.roi.size())
        return SensibleROI.from_points(pos, size)

    def remove_roi(self) -> None:
        self.image.vb.removeItem(self.roi)

    def _set_tof_range_label(self, range_min: int, range_max: int) -> None:
        self._tof_range_label.setText(f'ToF range: {range_min} - {range_max}')

    def _handle_tof_range_changed(self) -> None:
        tof_range = self.get_tof_range()
        self._set_tof_range_label(tof_range[0], tof_range[1])
        self.range_changed.emit(tof_range)
