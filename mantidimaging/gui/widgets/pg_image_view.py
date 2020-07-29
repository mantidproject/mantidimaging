from logging import getLogger
from typing import Optional, Tuple, Callable

import numpy as np
from PyQt5 import QtCore
from PyQt5.QtWidgets import QLabel
from pyqtgraph import ImageView, ROI, ImageItem
from pyqtgraph.GraphicsScene.mouseEvents import HoverEvent

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.core.utility.sensible_roi import SensibleROI


class UnrotateablePlotROI(ROI):
    """
    Like PlotROI but does not add a rotation handle.
    """

    def __init__(self, size):
        ROI.__init__(self, pos=[0, 0], size=size)
        self.addScaleHandle([1, 1], [0, 0])


class MIImageView(ImageView):
    details: QLabel
    roiString = None
    imageItem: ImageItem

    roi_changed_callback: Optional[Callable[[SensibleROI], None]] = None

    def __init__(self, parent=None, name="ImageView", view=None, imageItem=None, levelMode='mono', *args):
        super().__init__(parent, name, view, imageItem, levelMode, *args)
        self.details = QLabel("", self.ui.layoutWidget)
        self.details.setStyleSheet("QLabel { color : white; background-color: black}")
        self.ui.gridLayout.addWidget(self.details, 1, 0, 1, 1)

        self.imageItem.hoverEvent = self.image_hover_event
        # disconnect the ROI recalculation on every move
        self.roi.sigRegionChanged.disconnect(self.roiChanged)
        self.view.removeItem(self.roi)

        self.roi = UnrotateablePlotROI(300)
        self.roi.setZValue(30)
        # make ROI red
        self.roi.setPen((255, 0, 0))
        self.view.addItem(self.roi)
        self.roi.hide()
        self.roi.sigRegionChangeFinished.connect(self.roiChanged)
        self.extend_roi_plot_mouse_press_handler()
        self.imageItem.setAutoDownsample(False)

    def roiChanged(self):
        """
        Re-implements the roiChanged function to expect only 3D data,
        and uses a faster mean calculation on the ROI view of the data,
        instead of the full sized data.
        """
        # if the data isn't 3D the following code can't handle it correctly
        # so defer back to the original implementation which can handle 2D (any maybe ND)
        # more sensibly, albeit slower
        if self.image.ndim != 3:
            return super().roiChanged()

        roi_pos, roi_size = self.get_roi()

        # image indices are in order [Z, X, Y]
        left, right = roi_pos.x, roi_pos.x + roi_size.x
        top, bottom = roi_pos.y, roi_pos.y + roi_size.y

        data = self.image[:, top:bottom, left:right]
        if data is not None:
            while data.ndim > 1:
                data = data.mean(axis=1)
            if len(self.roiCurves) == 0:
                self.roiCurves.append(self.ui.roiPlot.plot())
            self.roiCurves[0].setData(y=data, x=self.tVals)

        self.roiString = f"({left}, {top}, {right}, {bottom}) | region avg={data[int(self.timeLine.value())].mean():.6f}"
        if self.roi_changed_callback:
            self.roi_changed_callback(SensibleROI(left, top, right, bottom))

    def extend_roi_plot_mouse_press_handler(self):
        original_handler = self.ui.roiPlot.mousePressEvent

        def extended_handler(ev):
            if ev.button() == QtCore.Qt.LeftButton:
                self.set_timeline_to_tick_nearest(ev.x())
            original_handler(ev)

        self.ui.roiPlot.mousePressEvent = lambda ev: extended_handler(ev)

    def get_roi(self, ensure_in_image=True) -> Tuple[CloseEnoughPoint, CloseEnoughPoint]:
        roi_pos, roi_size = CloseEnoughPoint(self.roi.pos()), CloseEnoughPoint(self.roi.size())

        if ensure_in_image:
            # Don't allow negative point coordinates
            if roi_pos.x < 0 or roi_pos.y < 0:
                getLogger(__name__).info("Region of Interest starts outside the picture! Clipping to image bounds")
                roi_pos.x = max(roi_pos.x, 0)
                roi_pos.y = max(roi_pos.y, 0)

            image_width = self.image.shape[1]
            image_height = self.image.shape[2]

            roi_right = roi_pos.x + roi_size.x
            roi_bottom = roi_pos.y + roi_size.y

            if roi_right > image_width:
                roi_size.x -= roi_right - image_width
            if roi_bottom > image_height:
                roi_size.y -= roi_bottom - image_height
        return roi_pos, roi_size

    def image_hover_event(self, event: HoverEvent):
        if event.exit:
            return
        pt = CloseEnoughPoint(event.pos())
        # event holds the coordinates in column-major coordinate
        # while the data is in row-major coordinate, hence why
        # the data access below is [y, x]
        msg = f"x={pt.y}, y={pt.x}, "
        if self.image.ndim == 3:
            msg += f"z={self.currentIndex}, value={self.image[self.currentIndex, pt.y, pt.x]:.6f}"
        else:
            msg += f"value={self.image[pt.y, pt.x]}"

        if self.roiString is not None:
            msg += f" | roi = {self.roiString}"

        self.details.setText(msg)

    def set_timeline_to_tick_nearest(self, x_pos_clicked):
        x_axis = self.getRoiPlot().getAxis('bottom')
        frac_pos = (x_pos_clicked - x_axis.x()) / x_axis.width()
        view_range = self.getRoiPlot().viewRange()[0]
        domain_pos = (view_range[1] - view_range[0]) * frac_pos
        self.timeLine.setValue(np.round(view_range[0] + domain_pos))
