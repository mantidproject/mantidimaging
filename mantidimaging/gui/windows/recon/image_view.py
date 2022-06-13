# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from math import isnan
from typing import Optional

import numpy as np
from PyQt5 import QtCore
from pyqtgraph import GraphicsLayoutWidget, InfiniteLine

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.core.utility.data_containers import Degrees
from mantidimaging.core.utility.histogram import set_histogram_log_scale
from mantidimaging.gui.widgets.line_profile_plot.view import LineProfilePlot
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView


class ReconImagesView(GraphicsLayoutWidget):
    sigSliceIndexChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.imageview_projection = MIMiniImageView(name="Projection", parent=parent)
        self.imageview_sinogram = MIMiniImageView(name="Sinogram", parent=parent)
        self.imageview_recon = MIMiniImageView(name="Recon", parent=parent, recon_mode=True)
        # Set the three images as axis siblings so that auto colour palette changes will be applied to them all
        MIMiniImageView.set_siblings([self.imageview_projection, self.imageview_sinogram, self.imageview_recon],
                                     axis=True)

        self.slice_line = InfiniteLine(pos=1024,
                                       angle=0,
                                       bounds=[0, self.imageview_projection.image_item.width()],
                                       movable=True)
        self.imageview_projection.viewbox.addItem(self.slice_line)
        self.tilt_line = InfiniteLine(pos=1024, angle=90, pen=(255, 0, 0, 255), movable=True)
        self.recon_line_profile = LineProfilePlot(self.imageview_recon)

        self.addItem(self.imageview_projection, 0, 0)
        self.addItem(self.imageview_recon, 0, 1)
        self.addItem(self.imageview_sinogram, 1, 0)
        self.addItem(self.recon_line_profile, 1, 1)

        self.imageview_projection.image_item.mouseClickEvent = lambda ev: self.mouse_click(ev, self.slice_line)
        self.slice_line.sigPositionChangeFinished.connect(self.slice_line_moved)

        # Work around for https://github.com/mantidproject/mantidimaging/issues/565
        self.scene().contextMenu = [item for item in self.scene().contextMenu if "export" not in item.text().lower()]

        self.imageview_projection.enable_nan_check()
        self.imageview_sinogram.enable_nan_check()
        self.imageview_recon.enable_nan_check()
        self.imageview_projection.enable_nonpositive_check()
        self.imageview_sinogram.enable_nonpositive_check()

    def slice_line_moved(self):
        self.slice_changed(int(self.slice_line.value()))

    def update_projection(self, image_data: np.ndarray, preview_slice_index: int, tilt_angle: Optional[Degrees]):
        self.imageview_projection.clear()
        self.imageview_projection.setImage(image_data)
        self.imageview_projection.histogram.imageChanged(autoLevel=True, autoRange=True)
        self.slice_line.setPos(preview_slice_index)
        if tilt_angle:
            self.set_tilt(tilt_angle, image_data.shape[1] // 2)
        else:
            self.hide_tilt()
        set_histogram_log_scale(self.imageview_projection.histogram)

    def update_sinogram(self, image):
        self.imageview_sinogram.clear()
        self.imageview_sinogram.setImage(image)
        self.imageview_sinogram.histogram.imageChanged(autoLevel=True, autoRange=True)
        set_histogram_log_scale(self.imageview_sinogram.histogram)

    def update_recon(self, image_data, reset_roi: bool = False):
        self.imageview_recon.clear()
        self.imageview_recon.setImage(image_data, autoLevels=False)
        set_histogram_log_scale(self.imageview_recon.histogram)
        if reset_roi:
            self.recon_line_profile.reset()
        else:
            self.recon_line_profile.update()

    def update_recon_hist(self):
        self.imageview_recon.histogram.imageChanged(autoLevel=True, autoRange=True)

    def mouse_click(self, ev, line: InfiniteLine):
        line.setPos(ev.pos())
        self.slice_changed(CloseEnoughPoint(ev.pos()).y)

    def slice_changed(self, slice_index):
        self.parent.presenter.do_preview_reconstruct_slice(slice_idx=slice_index)
        self.sigSliceIndexChanged.emit(slice_index)

    def clear_recon(self):
        self.imageview_recon.clear()

    def clear_recon_line_profile(self):
        self.recon_line_profile.clear_plot()

    def clear_sinogram(self):
        self.imageview_sinogram.clear()

    def clear_projection(self):
        self.imageview_projection.clear()

    def reset_slice_and_tilt(self, slice_index):
        self.slice_line.setPos(slice_index)
        self.hide_tilt()

    def hide_tilt(self):
        """
        Hides the tilt line. This stops infinite zooming out loop that messes up the image view
        (the line likes to be unbound when the degree isn't a multiple o 90 - and the tilt never is)
        :return:
        """
        if self.tilt_line.scene() is not None:
            self.imageview_projection.viewbox.removeItem(self.tilt_line)

    def set_tilt(self, tilt: Degrees, pos: Optional[int] = None):
        if not isnan(tilt.value):  # is isnan it means there is no tilt, i.e. the line is vertical
            if pos is not None:
                self.tilt_line.setAngle(90)
                self.tilt_line.setPos(pos)
            self.tilt_line.setAngle(90 + tilt.value)
        self.imageview_projection.viewbox.addItem(self.tilt_line)

    def reset_recon_histogram(self):
        self.imageview_recon.histogram.autoHistogramRange()
