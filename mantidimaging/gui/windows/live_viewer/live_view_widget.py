# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from pyqtgraph import GraphicsLayoutWidget, mkPen

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView
from mantidimaging.gui.widgets.zslider.zslider import ZSlider
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumROI

import numpy as np


class LiveViewWidget(GraphicsLayoutWidget):
    """
    The widget containing the spectrum plot and the image projection.

    @param parent: The parent widget
    """
    image: MIMiniImageView
    image_shape: tuple = (-1, -1)
    roi_changed = pyqtSignal()
    roi_changing = pyqtSignal()
    roi_object: SpectrumROI | None = None

    def __init__(self) -> None:
        super().__init__()

        self.image = MIMiniImageView(name="Projection")
        self.addItem(self.image, 0, 0)
        self.nextRow()

        self.z_slider = ZSlider()
        self.addItem(self.z_slider)

        self.image.enable_message()

        self.image.set_brightness_percentiles(0, 99)

    def show_image(self, image: np.ndarray) -> None:
        """
        Show the image in the image view.
        @param image: The image to show
        """
        self.image_shape = (np.shape(image)[0], np.shape(image)[1])
        self.image.setImage(image)

    def handle_deleted(self) -> None:
        """
        Handle the deletion of the image.
        """
        self.image.clear()

    def show_error(self, message: str | None) -> None:
        self.image.show_message(message)

    def add_roi(self) -> None:
        if self.image_shape == (-1, -1):
            return
        height, width = self.image_shape
        roi = SensibleROI.from_list([0, 0, width, height])
        self.roi_object = SpectrumROI('roi', roi, rotatable=False, scaleSnap=True, translateSnap=True)
        self.roi_object.colour = (255, 194, 10, 255)
        self.roi_object.hoverPen = mkPen(self.roi_object.colour, width=3)
        self.roi_object.roi.sigRegionChangeFinished.connect(self.roi_changed.emit)
        self.roi_object.roi.sigRegionChanged.connect(self.roi_changing.emit)
        self.image.vb.addItem(self.roi_object.roi)

    def set_image_shape(self, shape: tuple) -> None:
        self.image_shape = shape

    def get_roi(self) -> SensibleROI | None:
        if not self.roi_object:
            return None
        roi = self.roi_object.roi
        pos = CloseEnoughPoint(roi.pos())
        size = CloseEnoughPoint(roi.size())
        return SensibleROI.from_points(pos, size)

    def set_roi_visibility_flags(self, visible: bool) -> None:
        if not self.roi_object:
            return
        handles = self.roi_object.getHandles()
        for handle in handles:
            handle.setVisible(visible)
        self.roi_object.setVisible(visible)
